"""API key model for programmatic access."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class ApiKey(Base):
    """API key for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    prefix = Column(String(20), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scopes = Column(JSONB, default=list)
    rate_limit = Column(Integer, default=1000)
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSONB, default=dict)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)