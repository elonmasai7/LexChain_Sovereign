"""Asset and RWA tokenization models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AssetType(str, enum.Enum):
    REAL_ESTATE = "real_estate"
    CARBON_CREDIT = "carbon_credit"
    AGRICULTURE = "agriculture"
    ART = "art"
    COMMODITY = "commodity"


class AssetStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    MINTED = "minted"
    TRANSFERRED = "transferred"
    REVOKED = "revoked"


class Asset(Base):
    """Real World Asset model for tokenization."""
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    asset_type = Column(String(50), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    token_id = Column(String(255), nullable=True, index=True)
    contract_address = Column(String(255), nullable=True, index=True)
    chain_id = Column(Integer, nullable=True)
    total_supply = Column(Numeric(precision=78, decimal_places=0), nullable=True)
    circulating_supply = Column(Numeric(precision=78, decimal_places=0), default=0)
    fractional = Column(Boolean, default=False)
    legal_metadata = Column(JSONB, default=dict)
    compliance_rules = Column(JSONB, default=dict)
    verification_status = Column(String(50), default="unverified", index=True)
    custodian = Column(String(255), nullable=True)
    valuation = Column(Numeric(precision=20, decimal_places=2), nullable=True)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default=AssetStatus.DRAFT.value, nullable=False, index=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="assets", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_assets_owner_status", "owner_id", "status"),
        Index("idx_assets_type_status", "asset_type", "status"),
        Index("idx_assets_chain", "chain_id", "contract_address"),
    )

    def to_dict(self) -> dict:
        """Convert asset to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "asset_type": self.asset_type,
            "jurisdiction": self.jurisdiction,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "token_id": self.token_id,
            "contract_address": self.contract_address,
            "chain_id": self.chain_id,
            "total_supply": str(self.total_supply) if self.total_supply else None,
            "fractional": self.fractional,
            "verification_status": self.verification_status,
            "custodian": self.custodian,
            "valuation": str(self.valuation) if self.valuation else None,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AssetOwnership(Base):
    """Track ownership fractions of an asset."""
    __tablename__ = "asset_ownership"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shares = Column(Numeric(precision=78, decimal_places=0), nullable=False)
    acquisition_date = Column(DateTime(timezone=True), nullable=False)
    acquisition_price = Column(Numeric(precision=20, decimal_places=2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_ownership_asset_owner", "asset_id", "owner_id"),
        UniqueConstraint("asset_id", "owner_id", name="uq_asset_owner"),
    )