"""Governance and DAO models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    QUEUED = "queued"
    EXECUTED = "executed"
    DEFEATED = "defeated"
    CANCELED = "canceled"
    EXPIRED = "expired"


class VotingType(str, enum.Enum):
    SINGLE = "single"
    QUADRATIC = "quadratic"
    DELEGATED = "delegated"
   Weighted = "weighted"


class Proposal(Base):
    """DAO governance proposal model."""
    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    proposal_type = Column(String(50), nullable=False, index=True)
    voting_type = Column(String(50), default=VotingType.SINGLE.value, nullable=False)
    proposer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default=ProposalStatus.DRAFT.value, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    quorum = Column(Numeric(precision=5, decimal_places=2), default=10.0)
    quorum_required = Column(Boolean, default=True)
    votes_for = Column(Numeric(precision=78, decimal_places=0), default=0)
    votes_against = Column(Numeric(precision=78, decimal_places=0), default=0)
    abstentions = Column(Numeric(precision=78, decimal_places=0), default=0)
    total_votes = Column(Numeric(precision=78, decimal_places=0), default=0)
    execution_data = Column(JSONB, nullable=True)
    execution_hash = Column(String(255), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    proposer = relationship("User", back_populates="proposals")
    votes = relationship("Vote", back_populates="proposal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_proposal_status_time", "status", "start_time"),
        Index("idx_proposal_proposer", "proposer_id"),
    )

    @property
    def is_active(self) -> bool:
        """Check if proposal is currently open for voting."""
        if self.status != ProposalStatus.ACTIVE.value:
            return False
        now = datetime.now(timezone.utc)
        return (self.start_time <= now <= self.end_time) if self.start_time and self.end_time else False

    @property
    def approval_rate(self) -> float:
        """Calculate approval rate percentage."""
        if self.total_votes == 0:
            return 0.0
        return float(self.votes_for) / float(self.total_votes) * 100


class Vote(Base):
    """Vote on a governance proposal."""
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    voter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    choice = Column(String(20), nullable=False)
    weight = Column(Numeric(precision=78, decimal_places=0), default=1)
    voting_power = Column(Numeric(precision=78, decimal_places=0), default=1)
    quadratic_weight = Column(Numeric(precision=78, decimal_places=0), nullable=True)
    reason = Column(Text, nullable=True)
    delegation_id = Column(UUID(as_uuid=True), ForeignKey("delegations.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    proposal = relationship("Proposal", back_populates="votes")
    voter = relationship("User")

    __table_args__ = (
        Index("idx_vote_proposal_voter", "proposal_id", "voter_id", unique=True),
        Index("idx_vote_voter", "voter_id"),
    )


class Delegation(Base):
    """Voting power delegation."""
    __tablename__ = "delegations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delegator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    delegate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_amount = Column(Numeric(precision=78, decimal_places=0), default=0)
    voting_power = Column(Numeric(precision=78, decimal_places=0), default=1)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=True)
    expiry = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_delegation_delegator", "delegator_id"),
        Index("idx_delegation_delegate", "delegate_id"),
        Index("idx_delegation_active", "is_active"),
    )


class TreasuryTransaction(Base):
    """Treasury governance transactions."""
    __tablename__ = "treasury_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="SET NULL"), nullable=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Numeric(precision=78, decimal_places=0), nullable=False)
    token_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=False)
    from_address = Column(String(255), nullable=True)
    tx_hash = Column(String(255), nullable=True, index=True)
    status = Column(String(50), default="pending")
    executed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)