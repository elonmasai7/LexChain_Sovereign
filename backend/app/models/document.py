"""Legal document and smart contract models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DocumentType(str, enum.Enum):
    NDA = "nda"
    INVESTMENT_AGREEMENT = "investment_agreement"
    TOKEN_PURCHASE = "token_purchase"
    DAO_GOVERNANCE = "dao_governance"
    REAL_ESTATE = "real_estate"
    KYC_CONSENT = "kyc_consent"
    COMPLIANCE_DISCLOSURE = "compliance_disclosure"
    SERVICE_AGREEMENT = "service_agreement"
    PARTNERSHIP_AGREEMENT = "partnership_agreement"


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    COMPLETED = "completed"
    VOID = "void"
    EXPIRED = "expired"


class LegalDocument(Base):
    """Smart legal document model with blockchain anchoring support."""
    __tablename__ = "legal_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    content = Column(JSONB, default=dict)
    clauses = Column(JSONB, default=list)
    parties = Column(JSONB, default=list)
    status = Column(String(50), default=DocumentStatus.DRAFT.value, nullable=False, index=True)
    version = Column(String(20), default="1.0.0")
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id", ondelete="SET NULL"), nullable=True)
    ipfs_hash = Column(String(255), nullable=True, index=True)
    blockchain_tx_hash = Column(String(255), nullable=True, index=True)
    chain_id = Column(Integer, nullable=True)
    document_hash = Column(String(255), nullable=True, index=True)
    signature_data = Column(JSONB, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", back_populates="documents", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_documents_type_status", "document_type", "status"),
        Index("idx_documents_creator_status", "created_by", "status"),
        Index("idx_documents_chain", "blockchain_tx_hash", postgresql_where=blockchain_tx_hash.isnot(None)),
    )

    def to_dict(self) -> dict:
        """Convert document to dictionary representation."""
        return {
            "id": str(self.id),
            "title": self.title,
            "document_type": self.document_type,
            "jurisdiction": self.jurisdiction,
            "status": self.status,
            "version": self.version,
            "ipfs_hash": self.ipfs_hash,
            "blockchain_tx_hash": self.blockchain_tx_hash,
            "chain_id": self.chain_id,
            "document_hash": self.document_hash,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class DocumentSignature(Base):
    """Track signatures on documents."""
    __tablename__ = "document_signatures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("legal_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    signer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    signature_hash = Column(String(255), nullable=False)
    signature_data = Column(JSONB, nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_signature_doc_signer", "document_id", "signer_id"),
    )