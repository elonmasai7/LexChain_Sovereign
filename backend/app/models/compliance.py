"""Compliance and regulatory models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ComplianceStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ComplianceCheck(Base):
    """Compliance check tracking model."""
    __tablename__ = "compliance_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    check_type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default=ComplianceStatus.PENDING.value, nullable=False)
    result = Column(JSONB, default=dict)
    provider = Column(String(100), nullable=True)
    provider_ref_id = Column(String(255), nullable=True, index=True)
    score = Column(Numeric(precision=5, decimal_places=2), nullable=True)
    risk_level = Column(String(20), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="compliance_checks")

    __table_args__ = (
        Index("idx_compliance_user_type", "user_id", "check_type"),
        Index("idx_compliance_status", "status"),
    )


class SanctionHit(Base):
    """Sanctions screening hit model."""
    __tablename__ = "sanction_hits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    list_name = Column(String(100), nullable=False)
    matched_name = Column(String(255), nullable=False)
    matched_id = Column(String(255), nullable=True)
    match_score = Column(Numeric(precision=5, decimal_places=2), nullable=True)
    risk_level = Column(String(20), default="medium", nullable=False)
    details = Column(JSONB, default=dict)
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    false_positive = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_sanctions_user_risk", "user_id", "risk_level"),
        Index("idx_sanctions_reviewed", "reviewed"),
    )


class RiskScore(Base):
    """User risk score aggregation model."""
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Numeric(precision=5, decimal_places=2), nullable=False)
    category_scores = Column(JSONB, default=dict)
    factors = Column(JSONB, default=list)
    last_activity_score = Column(Numeric(precision=5, decimal_places=2), nullable=True)
    wallet_risk_score = Column(Numeric(precision=5, decimal_places=2), nullable=True)
    kyc_risk_score = Column(Numeric(precision=5, decimal_places=2), nullable=True)
    aml_risk_score = Column(Numeric(precision=5, decimal_places=2), nullable=True)
    risk_level = Column(String(20), nullable=False)
    risk_factors = Column(JSONB, default=list)
    recommendations = Column(JSONB, default=list)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    next_review_date = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_risk_user", "user_id", unique=True),
        Index("idx_risk_score_level", "risk_level"),
    )


class ComplianceEvent(Base):
    """Immutable compliance event log."""
    __tablename__ = "compliance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONB, default=dict)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    risk_level = Column(String(20), nullable=True)
    status = Column(String(50), default="open", index=True)
    resolution = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_compliance_event_user_type", "user_id", "event_type"),
    )