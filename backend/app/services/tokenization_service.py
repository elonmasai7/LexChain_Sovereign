"""RWA Tokenization service for Real World Assets."""
from datetime import datetime, timezone
from typing import Optional, list
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from web3 import Web3
from app.models.asset import Asset, AssetOwnership, AssetType, AssetStatus
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate, TokenizationRequest
from app.core.audit import audit_logger_service
from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)


class TokenizationService:
    """Real World Asset tokenization service."""

    CHAIN_IDS = {
        "ethereum": 1,
        "sepolia": 11155111,
        "polygon": 137,
        "base": 8453,
        "arbitrum": 42161
    }

    @staticmethod
    async def create_asset(db: AsyncSession, asset_data: AssetCreate, owner_id: str) -> Asset:
        """Create a new asset for tokenization."""
        asset = Asset(
            name=asset_data.name,
            description=asset_data.description,
            asset_type=asset_data.asset_type,
            jurisdiction=asset_data.jurisdiction,
            owner_id=owner_id,
            total_supply=asset_data.total_supply,
            fractional=asset_data.fractional,
            custodian=asset_data.custodian,
            valuation=asset_data.valuation,
            currency=asset_data.currency,
            legal_metadata=asset_data.legal_metadata or {},
            compliance_rules=asset_data.compliance_rules or {},
            status=AssetStatus.DRAFT.value
        )

        db.add(asset)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=owner_id, action="asset_create",
            resource_type="asset", resource_id=str(asset.id)
        )

        logger.info(f"Asset created: {asset.name} (ID: {asset.id})")
        return asset

    @staticmethod
    async def get_asset_by_id(db: AsyncSession, asset_id: str) -> Optional[Asset]:
        """Get asset by ID."""
        result = await db.execute(
            select(Asset).where(and_(Asset.id == asset_id, Asset.deleted_at.is_(None)))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_assets(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> tuple[list[Asset], int]:
        """List assets with filters."""
        query = select(Asset).where(Asset.deleted_at.is_(None))
        count_query = select(Asset).where(Asset.deleted_at.is_(None))

        if asset_type:
            query = query.where(Asset.asset_type == asset_type)
            count_query = count_query.where(Asset.asset_type == asset_type)

        if status:
            query = query.where(Asset.status == status)
            count_query = count_query.where(Asset.status == status)

        if jurisdiction:
            query = query.where(Asset.jurisdiction == jurisdiction)
            count_query = count_query.where(Asset.jurisdiction == jurisdiction)

        if owner_id:
            query = query.where(Asset.owner_id == owner_id)
            count_query = count_query.where(Asset.owner_id == owner_id)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Asset.created_at.desc())

        result = await db.execute(query)
        assets = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return assets, total

    @staticmethod
    async def update_asset(db: AsyncSession, asset: Asset, update_data: dict) -> Asset:
        """Update asset details."""
        for key, value in update_data.items():
            if hasattr(asset, key) and value is not None:
                setattr(asset, key, value)

        asset.updated_at = datetime.now(timezone.utc)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(asset.owner_id), action="asset_update",
            resource_type="asset", resource_id=str(asset.id)
        )

        return asset

    @staticmethod
    async def verify_asset(db: AsyncSession, asset: Asset, verification_type: str, documents: list[str] = None, notes: str = None) -> Asset:
        """Verify an asset for tokenization."""
        asset.verification_status = "in_review"
        asset.metadata["verification"] = {
            "type": verification_type,
            "documents": documents or [],
            "notes": notes,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        asset.updated_at = datetime.now(timezone.utc)

        await audit_logger_service.log_action(
            db, user_id=str(asset.owner_id), action="asset_verify",
            resource_type="asset", resource_id=str(asset.id),
            details={"verification_type": verification_type}
        )

        await db.flush()
        return asset

    @staticmethod
    async def approve_asset(db: AsyncSession, asset: Asset, approver_id: str) -> Asset:
        """Approve an asset for tokenization."""
        asset.verification_status = "verified"
        asset.status = AssetStatus.APPROVED.value
        asset.metadata["approval"] = {
            "approved_by": approver_id,
            "approved_at": datetime.now(timezone.utc).isoformat()
        }
        asset.updated_at = datetime.now(timezone.utc)

        await audit_logger_service.log_action(
            db, user_id=approver_id, action="asset_approve",
            resource_type="asset", resource_id=str(asset.id)
        )

        await db.flush()
        return asset

    @staticmethod
    async def mint_tokens(db: AsyncSession, asset: Asset, tokenization_request: TokenizationRequest, minter_id: str) -> Asset:
        """Mint tokens for an asset on the blockchain."""
        if asset.status != AssetStatus.APPROVED.value:
            raise ValueError("Asset must be approved before minting")

        web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))

        asset.chain_id = tokenization_request.chain_id
        asset.status = AssetStatus.MINTED.value
        asset.metadata["tokenization"] = {
            "chain_id": tokenization_request.chain_id,
            "initial_supply": str(tokenization_request.initial_supply or asset.total_supply),
            "transfer_restrictions": tokenization_request.transfer_restrictions,
            "compliance_enabled": tokenization_request.compliance_enabled,
            "minted_at": datetime.now(timezone.utc).isoformat(),
            "minted_by": minter_id
        }
        asset.updated_at = datetime.now(timezone.utc)

        await audit_logger_service.log_action(
            db, user_id=minter_id, action="asset_mint",
            resource_type="asset", resource_id=str(asset.id),
            details={"chain_id": tokenization_request.chain_id}
        )

        await db.flush()
        return asset

    @staticmethod
    async def transfer_ownership(db: AsyncSession, asset: Asset, new_owner_id: str, transferor_id: str) -> Asset:
        """Transfer asset ownership."""
        ownership = AssetOwnership(
            asset_id=asset.id,
            owner_id=new_owner_id,
            shares=asset.total_supply or 1,
            acquisition_date=datetime.now(timezone.utc),
            acquisition_price=asset.valuation
        )
        db.add(ownership)

        asset.owner_id = new_owner_id
        asset.status = AssetStatus.TRANSFERRED.value
        asset.metadata["transfer"] = {
            "from": transferor_id,
            "to": new_owner_id,
            "transferred_at": datetime.now(timezone.utc).isoformat()
        }
        asset.updated_at = datetime.now(timezone.utc)

        await audit_logger_service.log_action(
            db, user_id=transferor_id, action="asset_transfer",
            resource_type="asset", resource_id=str(asset.id),
            details={"new_owner": new_owner_id}
        )

        await db.flush()
        return asset

    @staticmethod
    async def validate_investor_eligibility(db: AsyncSession, investor_id: str, asset_type: str) -> tuple[bool, str]:
        """Check if an investor is eligible for a specific asset type."""
        result = await db.execute(select(User).where(User.id == investor_id))
        user = result.scalar_one_or_none()

        if not user:
            return False, "Investor not found"

        if not user.is_verified:
            return False, "Investor not verified"

        if user.role.value in ["investor", "asset_issuer"]:
            return True, "Eligible"

        return True, "Eligible with restrictions"

    @staticmethod
    async def get_asset_analytics(db: AsyncSession, asset_id: str) -> dict:
        """Get analytics for an asset."""
        result = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = result.scalar_one_or_none()

        if not asset:
            return {}

        ownership_result = await db.execute(
            select(AssetOwnership).where(AssetOwnership.asset_id == asset_id)
        )
        ownerships = list(ownership_result.scalars().all())

        return {
            "asset_id": str(asset.id),
            "asset_name": asset.name,
            "asset_type": asset.asset_type,
            "status": asset.status,
            "valuation": str(asset.valuation) if asset.valuation else None,
            "total_supply": str(asset.total_supply) if asset.total_supply else None,
            "circulating_supply": str(asset.circulating_supply) if asset.circulating_supply else None,
            "total_holders": len(ownerships),
            "jurisdiction": asset.jurisdiction,
            "created_at": asset.created_at.isoformat() if asset.created_at else None
        }

    @staticmethod
    async def revoke_asset(db: AsyncSession, asset: Asset, reason: str, revoker_id: str) -> Asset:
        """Revoke an asset tokenization."""
        asset.status = AssetStatus.REVOKED.value
        asset.metadata["revocation"] = {
            "reason": reason,
            "revoked_by": revoker_id,
            "revoked_at": datetime.now(timezone.utc).isoformat()
        }
        asset.updated_at = datetime.now(timezone.utc)

        await audit_logger_service.log_action(
            db, user_id=revoker_id, action="asset_revoke",
            resource_type="asset", resource_id=str(asset.id),
            details={"reason": reason}
        )

        await db.flush()
        return asset


tokenization_service = TokenizationService()