"""Document template model for smart legal contracts."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class DocumentTemplate(Base):
    """Template for legal documents with smart clause support."""
    __tablename__ = "document_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    content = Column(JSONB, default=dict)
    clauses = Column(JSONB, default=list)
    required_fields = Column(JSONB, default=list)
    default_values = Column(JSONB, default=dict)
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_template_type_jurisdiction", "template_type", "jurisdiction"),
        Index("idx_template_active", "is_active", "is_public"),
    )


class ClauseLibrary(Base):
    """Reusable legal clause library."""
    __tablename__ = "clause_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=True)
    clause_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    variables = Column(JSONB, default=list)
    risk_level = Column(String(20), default="low")
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    tags = Column(JSONB, default=list)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_clause_category_type", "category", "clause_type"),
    )