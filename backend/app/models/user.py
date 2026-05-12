"""User and authentication models."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Integer, Text,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    LEGAL_OFFICER = "legal_officer"
    COMPLIANCE_OFFICER = "compliance_officer"
    INVESTOR = "investor"
    DAO_MEMBER = "dao_member"
    ASSET_ISSUER = "asset_issuer"
    AUDITOR = "auditor"
    CLIENT = "client"


class User(Base):
    """User model with authentication and authorization fields."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    webauthn_credential_id = Column(String(512), nullable=True)
    webauthn_public_key = Column(Text, nullable=True)
    wallet_address = Column(String(255), nullable=True, index=True)
    did = Column(String(255), nullable=True, unique=True)
    full_name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    jurisdiction = Column(String(100), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    assets = relationship("Asset", back_populates="owner", foreign_keys="Asset.owner_id")
    documents = relationship("LegalDocument", back_populates="creator", foreign_keys="LegalDocument.created_by")
    proposals = relationship("Proposal", back_populates="proposer")
    compliance_checks = relationship("ComplianceCheck", back_populates="user")

    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_role_active", "role", "is_active"),
        Index("idx_users_wallet_active", "wallet_address", postgresql_where=wallet_address.isnot(None)),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    @property
    def is_locked(self) -> bool:
        """Check if user account is temporarily locked."""
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False

    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "full_name": self.full_name,
            "company": self.company,
            "jurisdiction": self.jurisdiction,
            "wallet_address": self.wallet_address,
            "did": self.did,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserSession(Base):
    """Session model for tracking user authentication sessions."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=True, index=True)
    device_fingerprint = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    rotated_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_active", "user_id", "is_active"),
        Index("idx_sessions_token_hash", "token_hash"),
    )