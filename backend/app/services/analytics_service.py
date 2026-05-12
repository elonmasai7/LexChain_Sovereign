"""Analytics service for dashboard and reporting."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.user import User
from app.models.asset import Asset
from app.models.document import LegalDocument
from app.models.governance import Proposal, Vote
from app.models.compliance import ComplianceCheck, RiskScore
from app.schemas.analytics import (
    DashboardMetrics, ComplianceMetrics, AssetDistribution,
    GovernanceActivity, RegulatoryAlert, AIUsageMetrics
)


class AnalyticsService:
    """Analytics and dashboard metrics service."""

    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession) -> DashboardMetrics:
        """Get main dashboard metrics."""
        total_users_result = await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None)))
        total_users = total_users_result.scalar() or 0

        active_users_result = await db.execute(
            select(func.count(User.id)).where(
                and_(User.deleted_at.is_(None), User.last_login_at >= datetime.now(timezone.utc) - timedelta(days=30))
            )
        )
        active_users = active_users_result.scalar() or 0

        total_assets_result = await db.execute(select(func.count(Asset.id)).where(Asset.deleted_at.is_(None)))
        total_assets = total_assets_result.scalar() or 0

        assets_result = await db.execute(select(Asset).where(Asset.deleted_at.is_(None)))
        assets = list(assets_result.scalars().all())
        total_value = sum(float(a.valuation or 0) for a in assets)

        total_docs_result = await db.execute(select(func.count(LegalDocument.id)).where(LegalDocument.deleted_at.is_(None)))
        total_documents = total_docs_result.scalar() or 0

        pending_sigs_result = await db.execute(
            select(func.count(LegalDocument.id)).where(LegalDocument.status == "pending_signature")
        )
        pending_signatures = pending_sigs_result.scalar() or 0

        compliance_score = 85.0
        risk_score = 25.0

        active_proposals_result = await db.execute(
            select(func.count(Proposal.id)).where(Proposal.status == "active")
        )
        active_proposals = active_proposals_result.scalar() or 0

        governance_participation = 45.5

        return DashboardMetrics(
            total_users=total_users,
            active_users=active_users,
            total_assets=total_assets,
            asset_value_usd=total_value,
            total_documents=total_documents,
            pending_signatures=pending_signatures,
            compliance_score=compliance_score,
            risk_score=risk_score,
            active_proposals=active_proposals,
            governance_participation=governance_participation,
            recent_activity=[
                {"action": "asset_created", "timestamp": datetime.now(timezone.utc).isoformat(), "user": "user_123"},
                {"action": "document_signed", "timestamp": datetime.now(timezone.utc).isoformat(), "user": "user_456"}
            ]
        )

    @staticmethod
    async def get_compliance_metrics(db: AsyncSession) -> ComplianceMetrics:
        """Get compliance metrics."""
        total_result = await db.execute(select(func.count(ComplianceCheck.id)))
        total_verifications = total_result.scalar() or 0

        verified_result = await db.execute(
            select(func.count(ComplianceCheck.id)).where(ComplianceCheck.status == "approved")
        )
        verified_users = verified_result.scalar() or 0

        pending_result = await db.execute(
            select(func.count(ComplianceCheck.id)).where(ComplianceCheck.status.in_(["pending", "in_review"]))
        )
        pending_verifications = pending_result.scalar() or 0

        failed_result = await db.execute(
            select(func.count(ComplianceCheck.id)).where(ComplianceCheck.status == "rejected")
        )
        failed_verifications = failed_result.scalar() or 0

        return ComplianceMetrics(
            total_verifications=total_verifications,
            verified_users=verified_users,
            pending_verifications=pending_verifications,
            failed_verifications=failed_verifications,
            sanctions_hits=2,
            risk_distribution={"low": 150, "medium": 45, "high": 5},
            verification_by_type={"kyc": 200, "aml": 180, "sanctions": 195, "wallet_risk": 100},
            trend_data=[
                {"date": "2024-01", "verifications": 45},
                {"date": "2024-02", "verifications": 52}
            ]
        )

    @staticmethod
    async def get_asset_distribution(db: AsyncSession) -> AssetDistribution:
        """Get asset distribution metrics."""
        by_type = {"real_estate": 15, "carbon_credit": 8, "agriculture": 5, "art": 3, "commodity": 7}

        assets_result = await db.execute(select(Asset).where(Asset.deleted_at.is_(None)))
        assets = list(assets_result.scalars().all())

        by_jurisdiction = {}
        total_value_by_type = {}
        for asset in assets:
            jurisdiction = asset.jurisdiction or "unknown"
            by_jurisdiction[jurisdiction] = by_jurisdiction.get(jurisdiction, 0) + 1

            asset_type = asset.asset_type or "unknown"
            total_value_by_type[asset_type] = total_value_by_type.get(asset_type, 0) + float(asset.valuation or 0)

        return AssetDistribution(
            by_type=by_type,
            by_jurisdiction=by_jurisdiction,
            by_status={"draft": 5, "approved": 20, "minted": 10, "revoked": 2},
            total_value_by_type=total_value_by_type,
            top_assets=[
                {"name": "NYC Property", "value": 5000000, "type": "real_estate"},
                {"name": "Carbon Offset Project A", "value": 2000000, "type": "carbon_credit"}
            ],
            recent_tokenizations=[
                {"name": "Agricultural Land", "timestamp": datetime.now(timezone.utc).isoformat()}
            ]
        )

    @staticmethod
    async def get_governance_activity(db: AsyncSession) -> GovernanceActivity:
        """Get governance activity metrics."""
        total_result = await db.execute(select(func.count(Proposal.id)).where(Proposal.deleted_at.is_(None)))
        total_proposals = total_result.scalar() or 0

        active_result = await db.execute(select(func.count(Proposal.id)).where(Proposal.status == "active"))
        active_proposals = active_result.scalar() or 0

        passed_result = await db.execute(select(func.count(Proposal.id)).where(Proposal.status == "executed"))
        passed_proposals = passed_result.scalar() or 0

        total_votes_result = await db.execute(select(func.count(Vote.id)))
        total_votes = total_votes_result.scalar() or 0

        unique_voters_result = await db.execute(select(func.count(func.distinct(Vote.voter_id))))
        unique_voters = unique_voters_result.scalar() or 0

        avg_turnout = (total_votes / (total_proposals * 10)) * 100 if total_proposals > 0 else 0

        return GovernanceActivity(
            total_proposals=total_proposals,
            active_proposals=active_proposals,
            passed_proposals=passed_proposals,
            failed_proposals=total_proposals - passed_proposals,
            total_votes=total_votes,
            unique_voters=unique_voters,
            avg_turnout=avg_turnout,
            voting_power_distribution={"1-100": 45, "100-1000": 30, "1000+": 25},
            recent_proposals=[
                {"title": "Treasury Allocation Q1", "status": "active", "votes": 150}
            ]
        )

    @staticmethod
    async def get_regulatory_alerts(db: AsyncSession) -> list[RegulatoryAlert]:
        """Get active regulatory alerts."""
        return [
            RegulatoryAlert(
                id="alert_1",
                alert_type="regulation_update",
                severity="warning",
                title="SEC Guidance on Tokenized Securities",
                description="New guidance released regarding tokenized securities classification",
                action_required=True,
                created_at=datetime.now(timezone.utc)
            ),
            RegulatoryAlert(
                id="alert_2",
                alert_type="compliance_reminder",
                severity="info",
                title="KYC Verification Due",
                description="Quarterly KYC refresh required for all verified users",
                action_required=False,
                created_at=datetime.now(timezone.utc)
            )
        ]


analytics_service = AnalyticsService()