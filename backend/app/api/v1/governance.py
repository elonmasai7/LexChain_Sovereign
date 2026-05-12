"""Governance and DAO API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.governance_service import GovernanceService
from app.schemas.governance import (
    ProposalCreate, ProposalResponse, ProposalListResponse,
    VoteRequest, VoteResponse, DelegationRequest, DelegationResponse
)
from app.models.user import User


router = APIRouter()


@router.get("/proposals", response_model=ProposalListResponse)
async def list_proposals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    proposal_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all governance proposals."""
    proposals, total = await GovernanceService.list_proposals(db, page, page_size, status, proposal_type)

    return ProposalListResponse(
        items=[ProposalResponse.model_validate(p) for p in proposals],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    proposal_data: ProposalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new governance proposal."""
    try:
        proposal = await GovernanceService.create_proposal(db, proposal_data, str(current_user.id))
        return proposal
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get proposal by ID."""
    proposal = await GovernanceService.get_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return proposal


@router.post("/proposals/{proposal_id}/activate")
async def activate_proposal(
    proposal_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate a proposal for voting."""
    from datetime import datetime, timezone, timedelta

    proposal = await GovernanceService.get_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    activated = await GovernanceService.activate_proposal(db, proposal, start, end)
    return {"message": "Proposal activated", "status": activated.status}


@router.post("/proposals/{proposal_id}/vote", response_model=VoteResponse)
async def cast_vote(
    proposal_id: str,
    vote_data: VoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cast a vote on a proposal."""
    proposal = await GovernanceService.get_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    if not proposal.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voting is not active")

    try:
        vote = await GovernanceService.cast_vote(db, proposal, vote_data, str(current_user.id))
        return vote
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/proposals/{proposal_id}/execute")
async def execute_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a passed proposal."""
    proposal = await GovernanceService.get_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    try:
        executed = await GovernanceService.execute_proposal(db, proposal, str(current_user.id))
        return {"message": "Proposal executed", "status": executed.status, "execution_hash": executed.execution_hash}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/proposals/{proposal_id}/tally")
async def get_vote_tally(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get vote tally for a proposal."""
    tally = await GovernanceService.tally_votes(db, proposal_id)
    if not tally:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return tally


@router.post("/delegate", response_model=DelegationResponse)
async def delegate_vote(
    delegation_data: DelegationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delegate voting power to another user."""
    try:
        delegation = await GovernanceService.delegate_vote(db, delegation_data, str(current_user.id))
        return delegation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/delegations")
async def get_delegations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's delegations."""
    from app.models.governance import Delegation
    from sqlalchemy import select

    result = await db.execute(
        select(Delegation).where(Delegation.delegator_id == current_user.id)
    )
    delegations = list(result.scalars().all())
    return [DelegationResponse.model_validate(d) for d in delegations]


@router.get("/votes/history")
async def get_voting_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's voting history."""
    history = await GovernanceService.get_voter_history(db, str(current_user.id), limit)
    return [{"proposal_id": str(v.proposal_id), "choice": v.choice, "weight": str(v.weight)} for v in history]