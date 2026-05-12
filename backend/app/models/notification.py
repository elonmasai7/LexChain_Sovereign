"""Notification model for in-app notifications."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import enum


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DOCUMENT_SIGNED = "document_signed"
    COMPLIANCE_ALERT = "compliance_alert"
    PROPOSAL_CREATED = "proposal_created"
    VOTE_RECEIVED = "vote_received"
    ASSET_MINTED = "asset_minted"


class Notification(Base):
    """In-app notification model."""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default=NotificationType.INFO.value, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    action_url = Column(String(512), nullable=True)
    action_label = Column(String(100), nullable=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_notification_user_read", "user_id", "is_read"),
        Index("idx_notification_created", "created_at"),
    )