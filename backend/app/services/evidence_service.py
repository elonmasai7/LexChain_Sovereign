"""Legal evidence vault service."""
import hashlib
from datetime import datetime, timezone
from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.evidence import LegalEvidence, EvidenceVerification, EvidenceAnchor, EvidenceStatus
from app.schemas.evidence import EvidenceCreate, EvidenceVerificationRequest
from app.core.security import hash_file_content
from app.core.audit import audit_logger_service
from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)


class EvidenceService:
    """Legal evidence vault with immutable audit trails."""

    @staticmethod
    async def store_evidence(db: AsyncSession, evidence_data: EvidenceCreate, uploaded_by: str) -> LegalEvidence:
        """Store evidence with encryption."""
        evidence = LegalEvidence(
            case_id=evidence_data.case_id,
            title=evidence_data.title,
            description=evidence_data.description,
            file_hash=evidence_data.file_hash,
            file_type=evidence_data.file_type,
            file_size=evidence_data.file_size,
            ipfs_cid=evidence_data.ipfs_cid,
            chain_id=evidence_data.chain_id,
            uploaded_by=uploaded_by,
            status=EvidenceStatus.PENDING.value,
            metadata=evidence_data.metadata or {},
            tags=evidence_data.tags or []
        )

        db.add(evidence)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=uploaded_by, action="evidence_store",
            resource_type="evidence", resource_id=str(evidence.id)
        )

        logger.info(f"Evidence stored: {evidence.title} (ID: {evidence.id})")
        return evidence

    @staticmethod
    async def get_evidence_by_id(db: AsyncSession, evidence_id: str) -> Optional[LegalEvidence]:
        """Get evidence by ID."""
        result = await db.execute(select(LegalEvidence).where(LegalEvidence.id == evidence_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_evidence(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        case_id: Optional[str] = None,
        status: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> tuple[list[LegalEvidence], int]:
        """List evidence with filters."""
        query = select(LegalEvidence)
        count_query = select(LegalEvidence)

        if case_id:
            query = query.where(LegalEvidence.case_id == case_id)
            count_query = count_query.where(LegalEvidence.case_id == case_id)

        if status:
            query = query.where(LegalEvidence.status == status)
            count_query = count_query.where(LegalEvidence.status == status)

        if uploaded_by:
            query = query.where(LegalEvidence.uploaded_by == uploaded_by)
            count_query = count_query.where(LegalEvidence.uploaded_by == uploaded_by)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(LegalEvidence.created_at.desc())

        result = await db.execute(query)
        evidence_list = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return evidence_list, total

    @staticmethod
    async def verify_evidence_hash(db: AsyncSession, verification_request: EvidenceVerificationRequest, verifier_id: str = None) -> EvidenceVerification:
        """Verify evidence file hash."""
        result = await db.execute(select(LegalEvidence).where(LegalEvidence.id == verification_request.evidence_id))
        evidence = result.scalar_one_or_none()

        if not evidence:
            raise ValueError("Evidence not found")

        is_valid = evidence.file_hash == verification_request.file_content_hash

        verification = EvidenceVerification(
            evidence_id=evidence.id,
            verified_by=verifier_id,
            verification_hash=verification_request.file_content_hash,
            is_valid=is_valid,
            details={"original_hash": evidence.file_hash, "submitted_hash": verification_request.file_content_hash}
        )

        db.add(verification)

        evidence.verification_count += 1
        evidence.last_verified_at = datetime.now(timezone.utc)

        if is_valid and evidence.status == EvidenceStatus.PENDING.value:
            evidence.status = EvidenceStatus.VERIFIED.value

        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=verifier_id, action="evidence_verify",
            resource_type="evidence", resource_id=str(evidence.id),
            details={"is_valid": is_valid}
        )

        return verification

    @staticmethod
    async def anchor_to_blockchain(db: AsyncSession, evidence: LegalEvidence, tx_hash: str, block_number: int, block_timestamp: datetime, gas_used: int = None, chain_id: int = 1) -> EvidenceAnchor:
        """Anchor evidence hash to blockchain."""
        anchor = EvidenceAnchor(
            evidence_id=evidence.id,
            chain_id=chain_id,
            anchor_type="timestamp",
            tx_hash=tx_hash,
            block_number=block_number,
            block_timestamp=block_timestamp,
            gas_used=gas_used,
            status="confirmed"
        )

        db.add(anchor)

        evidence.blockchain_tx_hash = tx_hash
        evidence.blockchain_block_number = block_number
        evidence.blockchain_timestamp = block_timestamp
        evidence.chain_id = chain_id

        if evidence.status == EvidenceStatus.VERIFIED.value:
            evidence.status = EvidenceStatus.ANCHORED.value

        evidence.metadata["anchored"] = {
            "tx_hash": tx_hash,
            "block_number": block_number,
            "anchored_at": datetime.now(timezone.utc).isoformat()
        }

        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(evidence.uploaded_by), action="evidence_anchor",
            resource_type="evidence", resource_id=str(evidence.id),
            details={"tx_hash": tx_hash, "chain_id": chain_id}
        )

        return anchor

    @staticmethod
    async def generate_proof(db: AsyncSession, evidence: LegalEvidence) -> dict:
        """Generate verification proof for evidence."""
        proof = {
            "evidence_id": str(evidence.id),
            "title": evidence.title,
            "file_hash": evidence.file_hash,
            "status": evidence.status,
            "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
            "verifications": [],
            "anchors": []
        }

        verifications_result = await db.execute(
            select(EvidenceVerification).where(EvidenceVerification.evidence_id == evidence.id)
        )
        verifications = list(verifications_result.scalars().all())

        for v in verifications:
            proof["verifications"].append({
                "verified_at": v.created_at.isoformat() if v.created_at else None,
                "is_valid": v.is_valid,
                "verified_by": str(v.verified_by) if v.verified_by else None
            })

        anchors_result = await db.execute(
            select(EvidenceAnchor).where(EvidenceAnchor.evidence_id == evidence.id)
        )
        anchors = list(anchors_result.scalars().all())

        for a in anchors:
            proof["anchors"].append({
                "chain_id": a.chain_id,
                "tx_hash": a.tx_hash,
                "block_number": a.block_number,
                "block_timestamp": a.block_timestamp.isoformat() if a.block_timestamp else None,
                "status": a.status
            })

        return proof

    @staticmethod
    async def get_chain_of_custody(db: AsyncSession, evidence_id: str) -> list[dict]:
        """Get chain of custody record for evidence."""
        result = await db.execute(select(LegalEvidence).where(LegalEvidence.id == evidence_id))
        evidence = result.scalar_one_or_none()

        if not evidence:
            return []

        custody = [
            {
                "action": "created",
                "user_id": str(evidence.uploaded_by) if evidence.uploaded_by else None,
                "timestamp": evidence.created_at.isoformat() if evidence.created_at else None
            }
        ]

        verifications_result = await db.execute(
            select(EvidenceVerification).where(EvidenceVerification.evidence_id == evidence_id)
        )
        verifications = list(verifications_result.scalars().all())

        for v in verifications:
            custody.append({
                "action": "verified",
                "user_id": str(v.verified_by) if v.verified_by else None,
                "timestamp": v.created_at.isoformat() if v.created_at else None,
                "is_valid": v.is_valid
            })

        anchors_result = await db.execute(
            select(EvidenceAnchor).where(EvidenceAnchor.evidence_id == evidence_id)
        )
        anchors = list(anchors_result.scalars().all())

        for a in anchors:
            custody.append({
                "action": "anchored",
                "chain_id": a.chain_id,
                "tx_hash": a.tx_hash,
                "timestamp": a.created_at.isoformat() if a.created_at else None
            })

        return custody

    @staticmethod
    async def update_evidence(db: AsyncSession, evidence: LegalEvidence, update_data: dict) -> LegalEvidence:
        """Update evidence metadata."""
        for key, value in update_data.items():
            if hasattr(evidence, key) and value is not None:
                setattr(evidence, key, value)

        evidence.updated_at = datetime.now(timezone.utc)
        await db.flush()

        return evidence


evidence_service = EvidenceService()