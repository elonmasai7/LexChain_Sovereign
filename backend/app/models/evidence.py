"""Legal evidence and document vault models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, BigInteger, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import enum


class EvidenceStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    ANCHORED = "anchored"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class LegalEvidence(Base):
    """Legal evidence vault model for immutable audit trails."""
    __tablename__ = "legal_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_hash = Column(String(255), nullable=False, index=True)
    ipfs_cid = Column(String(255), nullable=True, index=True)
    ipfs_dag_size = Column(BigInteger, nullable=True)
    blockchain_tx_hash = Column(String(255), nullable=True, index=True)
    blockchain_block_number = Column(Integer, nullable=True)
    blockchain_timestamp = Column(DateTime(timezone=True), nullable=True)
    chain_id = Column(Integer, nullable=True)
    encryption_key_hash = Column(String(255), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default=EvidenceStatus.PENDING.value, nullable=False)
    verification_count = Column(Integer, default=0)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    tags = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_evidence_case_status", "case_id", "status"),
        Index("idx_evidence_hash", "file_hash"),
        Index("idx_evidence_uploader", "uploaded_by"),
        Index("idx_evidence_created", "created_at"),
    )


class EvidenceVerification(Base):
    """Evidence verification records."""
    __tablename__ = "evidence_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("legal_evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verification_hash = Column(String(255), nullable=False)
    is_valid = Column(Boolean, nullable=False)
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class EvidenceAnchor(Base):
    """Blockchain anchoring records for evidence."""
    __tablename__ = "evidence_anchors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("legal_evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    chain_id = Column(Integer, nullable=False)
    anchor_type = Column(String(50), nullable=False)
    tx_hash = Column(String(255), nullable=False)
    block_number = Column(Integer, nullable=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=True)
    gas_used = Column(BigInteger, nullable=True)
    gas_price = Column(BigInteger, nullable=True)
    status = Column(String(50), default="pending")
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)