"""Governance and DAO service."""
from datetime import datetime, timezone
from typing import Optional, list
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.governance import Proposal, Vote, Delegation, TreasuryTransaction, ProposalStatus, VotingType
from app.models.user import User
from app.schemas.governance import ProposalCreate, VoteRequest, DelegationRequest
from app.core.audit import audit_logger_service
from app.core.logging import get_logger


logger = get_logger(__name__)


class GovernanceService:
    """DAO governance service."""

    @staticmethod
    async def create_proposal(db: AsyncSession, proposal_data: ProposalCreate, proposer_id: str) -> Proposal:
        """Create a new governance proposal."""
        proposal = Proposal(
            title=proposal_data.title,
            description=proposal_data.description,
            proposal_type=proposal_data.proposal_type,
            voting_type=proposal_data.voting_type,
            proposer_id=proposer_id,
            quorum=Decimal(str(proposal_data.quorum or 10.0)),
            execution_data=proposal_data.execution_data,
            metadata=proposal_data.metadata or {},
            status=ProposalStatus.DRAFT.value
        )

        db.add(proposal)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=proposer_id, action="proposal_create",
            resource_type="proposal", resource_id=str(proposal.id)
        )

        logger.info(f"Proposal created: {proposal.title} (ID: {proposal.id})")
        return proposal

    @staticmethod
    async def get_proposal(db: AsyncSession, proposal_id: str) -> Optional[Proposal]:
        """Get proposal by ID."""
        result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_proposals(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        proposal_type: Optional[str] = None
    ) -> tuple[list[Proposal], int]:
        """List proposals with filters."""
        query = select(Proposal).where(Proposal.deleted_at.is_(None))
        count_query = select(Proposal).where(Proposal.deleted_at.is_(None))

        if status:
            query = query.where(Proposal.status == status)
            count_query = count_query.where(Proposal.status == status)

        if proposal_type:
            query = query.where(Proposal.proposal_type == proposal_type)
            count_query = count_query.where(Proposal.proposal_type == proposal_type)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Proposal.created_at.desc())

        result = await db.execute(query)
        proposals = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return proposals, total

    @staticmethod
    async def activate_proposal(db: AsyncSession, proposal: Proposal, start_time: datetime = None, end_time: datetime = None) -> Proposal:
        """Activate a proposal for voting."""
        proposal.status = ProposalStatus.ACTIVE.value
        proposal.start_time = start_time or datetime.now(timezone.utc)
        proposal.end_time = end_time or (proposal.start_time.replace(hour=proposal.start_time.hour + 72))

        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(proposal.proposer_id), action="proposal_activate",
            resource_type="proposal", resource_id=str(proposal.id)
        )

        return proposal

    @staticmethod
    async def cast_vote(db: AsyncSession, proposal: Proposal, vote_data: VoteRequest, voter_id: str) -> Vote:
        """Cast a vote on a proposal."""
        existing_vote = await db.execute(
            select(Vote).where(and_(Vote.proposal_id == proposal.id, Vote.voter_id == voter_id))
        )
        if existing_vote.scalar_one_or_none():
            raise ValueError("Already voted on this proposal")

        weight = Decimal(str(vote_data.weight or 1))
        voting_power = weight

        if proposal.voting_type == VotingType.QUADRATIC.value:
            voting_power = Decimal(str(int(float(weight) ** 0.5)))

        vote = Vote(
            proposal_id=proposal.id,
            voter_id=voter_id,
            choice=vote_data.choice,
            weight=weight,
            voting_power=voting_power,
            quadratic_weight=voting_power if proposal.voting_type == VotingType.QUADRATIC.value else None,
            reason=vote_data.reason
        )

        db.add(vote)

        if vote_data.choice == "for":
            proposal.votes_for += int(voting_power)
        elif vote_data.choice == "against":
            proposal.votes_against += int(voting_power)
        else:
            proposal.abstentions += int(voting_power)

        proposal.total_votes += int(voting_power)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=voter_id, action="vote_cast",
            resource_type="proposal", resource_id=str(proposal.id),
            details={"choice": vote_data.choice, "weight": str(weight)}
        )

        return vote

    @staticmethod
    async def execute_proposal(db: AsyncSession, proposal: Proposal, executor_id: str) -> Proposal:
        """Execute a passed proposal."""
        if proposal.status != ProposalStatus.ACTIVE.value:
            raise ValueError("Proposal is not active")

        now = datetime.now(timezone.utc)
        if proposal.end_time > now:
            raise ValueError("Voting period has not ended")

        approval_rate = float(proposal.votes_for) / float(proposal.total_votes) if proposal.total_votes > 0 else 0

        if approval_rate < 0.5:
            proposal.status = ProposalStatus.DEFEATED.value
        else:
            proposal.status = ProposalStatus.EXECUTED.value
            proposal.executed_at = datetime.now(timezone.utc)
            proposal.execution_hash = f"0x{hashlib.hexencode(os.urandom(32)).decode()}"

            if proposal.execution_data:
                await GovernanceService._execute_execution_data(proposal.execution_data, db, proposal)

        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=executor_id, action="proposal_execute",
            resource_type="proposal", resource_id=str(proposal.id)
        )

        return proposal

    @staticmethod
    async def _execute_execution_data(execution_data: dict, db: AsyncSession, proposal: Proposal):
        """Execute the data associated with a proposal."""
        if execution_data.get("type") == "token_transfer":
            tx = TreasuryTransaction(
                proposal_id=proposal.id,
                transaction_type="transfer",
                amount=Decimal(str(execution_data.get("amount", 0))),
                to_address=execution_data.get("to_address", ""),
                status="pending"
            )
            db.add(tx)
            await db.flush()

    @staticmethod
    async def delegate_vote(db: AsyncSession, delegation_data: DelegationRequest, delegator_id: str) -> Delegation:
        """Delegate voting power to another user."""
        delegate_result = await db.execute(select(User).where(User.id == delegation_data.delegate_id))
        delegate = delegate_result.scalar_one_or_none()
        if not delegate:
            raise ValueError("Delegate not found")

        delegation = Delegation(
            delegator_id=delegator_id,
            delegate_id=delegation_data.delegate_id,
            token_amount=delegation_data.token_amount,
            voting_power=Decimal(str(delegation_data.token_amount or 1)),
            proposal_id=delegation_data.proposal_id,
            expiry=delegation_data.expiry,
            is_active=True
        )

        db.add(delegation)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=delegator_id, action="vote_delegate",
            resource_type="delegation", resource_id=str(delegation.id),
            details={"delegate": delegation_data.delegate_id}
        )

        return delegation

    @staticmethod
    async def tally_votes(db: AsyncSession, proposal_id: str) -> dict:
        """Get vote tally for a proposal."""
        result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
        proposal = result.scalar_one_or_none()

        if not proposal:
            return {}

        return {
            "proposal_id": str(proposal.id),
            "votes_for": str(proposal.votes_for),
            "votes_against": str(proposal.votes_against),
            "abstentions": str(proposal.abstentions),
            "total_votes": str(proposal.total_votes),
            "approval_rate": float(proposal.votes_for) / float(proposal.total_votes) * 100 if proposal.total_votes > 0 else 0,
            "quorum_met": float(proposal.total_votes) >= float(proposal.quorum)
        }

    @staticmethod
    async def get_voter_history(db: AsyncSession, voter_id: str, limit: int = 50) -> list[Vote]:
        """Get voting history for a user."""
        result = await db.execute(
            select(Vote).where(Vote.voter_id == voter_id).order_by(Vote.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


import hashlib
import os

governance_service = GovernanceService()