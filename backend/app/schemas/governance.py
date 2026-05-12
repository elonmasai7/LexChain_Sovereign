"""Governance-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    """Schema for creating a governance proposal."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    proposal_type: str = Field(..., description="token_transfer, parameter_change, plugin, custom")
    voting_type: str = "single"
    quorum: Optional[float] = Field(default=10.0, ge=0, le=100)
    execution_data: Optional[dict] = None
    metadata: Optional[dict] = None


class ProposalUpdate(BaseModel):
    """Schema for updating a proposal."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    execution_data: Optional[dict] = None
    metadata: Optional[dict] = None


class ProposalResponse(BaseModel):
    """Proposal response schema."""
    id: str
    title: str
    description: str
    proposal_type: str
    voting_type: str
    proposer_id: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    quorum: float
    votes_for: str
    votes_against: str
    abstentions: str
    total_votes: str
    approval_rate: float
    execution_hash: Optional[str] = None
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class ProposalListResponse(BaseModel):
    """Paginated proposal list."""
    items: list[ProposalResponse]
    total: int
    page: int
    page_size: int


class VoteRequest(BaseModel):
    """Vote on a proposal."""
    proposal_id: str
    choice: str = Field(..., description="for, against, abstain")
    weight: Optional[int] = Field(default=1, ge=1)
    reason: Optional[str] = Field(None, max_length=500)


class VoteResponse(BaseModel):
    """Vote response."""
    id: str
    proposal_id: str
    voter_id: str
    choice: str
    weight: int
    voting_power: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DelegationRequest(BaseModel):
    """Voting power delegation request."""
    delegate_id: str
    token_amount: Optional[Decimal] = None
    proposal_id: Optional[str] = None
    expiry: Optional[datetime] = None


class DelegationResponse(BaseModel):
    """Delegation response."""
    id: str
    delegator_id: str
    delegate_id: str
    token_amount: Optional[str] = None
    voting_power: int
    is_active: bool
    expiry: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TreasuryBalanceResponse(BaseModel):
    """Treasury balance response."""
    total_value_usd: float
    tokens: list[dict]
    recent_transactions: list[dict]


class GovernanceMetricsResponse(BaseModel):
    """Governance metrics response."""
    active_proposals: int
    total_proposals: int
    total_votes: int
    unique_voters: int
    avg_turnout: float
    treasury_value_usd: float