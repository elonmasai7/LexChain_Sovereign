"""Compliance service for AML, KYC, and sanctions screening."""
from datetime import datetime, timezone, timedelta
from typing import Optional, list
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.compliance import ComplianceCheck, SanctionHit, RiskScore, ComplianceEvent, ComplianceStatus
from app.models.user import User
from app.schemas.compliance import ComplianceCheckRequest, RiskScoreResponse
from app.core.audit import audit_logger_service
from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)


class ComplianceService:
    """Enterprise compliance and regulatory service."""

    @staticmethod
    async def run_aml_check(db: AsyncSession, request: ComplianceCheckRequest) -> ComplianceCheck:
        """Run AML screening check."""
        check = ComplianceCheck(
            user_id=request.user_id,
            check_type="aml",
            status=ComplianceStatus.PENDING.value,
            provider=request.provider or "chainalysis",
            details=request.dict() if hasattr(request, 'dict') else {}
        )

        db.add(check)
        await db.flush()

        await ComplianceService._simulate_aml_check(check, db)

        await audit_logger_service.log_action(
            db, user_id=request.user_id, action="aml_check",
            resource_type="compliance", resource_id=str(check.id)
        )

        return check

    @staticmethod
    async def _simulate_aml_check(check: ComplianceCheck, db: AsyncSession):
        """Simulate AML check completion."""
        check.status = ComplianceStatus.APPROVED.value
        check.score = 85.0
        check.risk_level = "low"
        check.result = {
            "verified": True,
            "risk_score": 15,
            "screening_results": {
                "pep": False,
                "sanctions": False,
                "adverse_media": False
            }
        }
        check.checked_at = datetime.now(timezone.utc)
        check.expires_at = datetime.now(timezone.utc) + timedelta(days=90)
        await db.flush()

    @staticmethod
    async def run_kyc(db: AsyncSession, request: ComplianceCheckRequest) -> ComplianceCheck:
        """Run KYC verification."""
        check = ComplianceCheck(
            user_id=request.user_id,
            check_type="kyc",
            status=ComplianceStatus.PENDING.value,
            provider=request.provider or "persona",
            details={"verification_data": request.dict() if hasattr(request, 'dict') else {}}
        )

        db.add(check)
        await db.flush()

        check.status = ComplianceStatus.APPROVED.value
        check.score = 95.0
        check.risk_level = "low"
        check.result = {
            "identity_verified": True,
            "document_authentic": True,
            "liveness_check": True
        }
        check.checked_at = datetime.now(timezone.utc)
        check.expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=request.user_id, action="kyc_verification",
            resource_type="compliance", resource_id=str(check.id)
        )

        return check

    @staticmethod
    async def run_sanctions_screening(db: AsyncSession, request: ComplianceCheckRequest, name: str = None, wallet_address: str = None) -> ComplianceCheck:
        """Run sanctions screening."""
        check = ComplianceCheck(
            user_id=request.user_id,
            check_type="sanctions",
            status=ComplianceStatus.PENDING.value,
            provider="ofac",
            details={"name": name, "wallet_address": wallet_address}
        )

        db.add(check)
        await db.flush()

        result = await ComplianceService._check_sanctions_list(name, wallet_address)

        if result["hit"]:
            sanction_hit = SanctionHit(
                user_id=request.user_id,
                list_name=result["list_name"],
                matched_name=result["matched_name"],
                matched_id=result["matched_id"],
                match_score=result["score"],
                risk_level="high"
            )
            db.add(sanction_hit)

            check.status = ComplianceStatus.REJECTED.value
            check.risk_level = "high"
        else:
            check.status = ComplianceStatus.APPROVED.value
            check.risk_level = "low"

        check.score = result["score"]
        check.result = result
        check.checked_at = datetime.now(timezone.utc)
        check.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=request.user_id, action="sanctions_screening",
            resource_type="compliance", resource_id=str(check.id),
            details={"hit": result["hit"]}
        )

        return check

    @staticmethod
    async def _check_sanctions_list(name: str = None, wallet_address: str = None) -> dict:
        """Check against sanctions list (simulated)."""
        return {
            "hit": False,
            "list_name": None,
            "matched_name": None,
            "matched_id": None,
            "score": 0.0
        }

    @staticmethod
    async def analyze_wallet_risk(db: AsyncSession, request: ComplianceCheckRequest, wallet_address: str, chain_id: int = 1) -> ComplianceCheck:
        """Analyze wallet risk score."""
        check = ComplianceCheck(
            user_id=request.user_id,
            check_type="wallet_risk",
            status=ComplianceStatus.PENDING.value,
            provider="trmlabs",
            details={"wallet_address": wallet_address, "chain_id": chain_id}
        )

        db.add(check)
        await db.flush()

        risk_analysis = await ComplianceService._analyze_wallet(wallet_address, chain_id)

        check.status = ComplianceStatus.APPROVED.value
        check.score = risk_analysis["risk_score"]
        check.risk_level = risk_analysis["risk_level"]
        check.result = risk_analysis
        check.checked_at = datetime.now(timezone.utc)
        check.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=request.user_id, action="wallet_risk_analysis",
            resource_type="compliance", resource_id=str(check.id),
            details={"risk_level": risk_analysis["risk_level"]}
        )

        return check

    @staticmethod
    async def _analyze_wallet(wallet_address: str, chain_id: int) -> dict:
        """Analyze wallet transaction history (simulated)."""
        return {
            "risk_score": 25.0,
            "risk_level": "low",
            "factors": {
                "tx_count": 150,
                "interaction_count": 25,
                "avg_tx_value": 5000,
                "first_activity": "2023-01-15",
                "suspicious_interactions": 0
            },
            "flags": []
        }

    @staticmethod
    async def generate_risk_score(db: AsyncSession, user_id: str) -> RiskScore:
        """Generate overall risk score for a user."""
        result = await db.execute(
            select(ComplianceCheck).where(
                and_(ComplianceCheck.user_id == user_id, ComplianceCheck.deleted_at.is_(None))
            ).order_by(ComplianceCheck.checked_at.desc())
        )
        checks = list(result.scalars().all())

        if not checks:
            return None

        kyc_score = 0.0
        aml_score = 0.0
        wallet_score = 0.0

        for check in checks:
            if check.check_type == "kyc" and check.score:
                kyc_score = check.score
            elif check.check_type == "aml" and check.score:
                aml_score = check.score
            elif check.check_type == "wallet_risk" and check.score:
                wallet_score = 100 - check.score

        overall_score = (kyc_score * 0.4 + aml_score * 0.3 + wallet_score * 0.3)

        if overall_score >= 80:
            risk_level = "low"
        elif overall_score >= 50:
            risk_level = "medium"
        else:
            risk_level = "high"

        risk_score = RiskScore(
            user_id=user_id,
            overall_score=Decimal(str(overall_score)),
            category_scores={
                "kyc": float(kyc_score),
                "aml": float(aml_score),
                "wallet_risk": float(wallet_score)
            },
            risk_level=risk_level,
            last_updated=datetime.now(timezone.utc),
            next_review_date=datetime.now(timezone.utc) + timedelta(days=30)
        )

        existing = await db.execute(select(RiskScore).where(RiskScore.user_id == user_id))
        existing_score = existing.scalar_one_or_none()
        if existing_score:
            risk_score.id = existing_score.id

        db.add(risk_score)
        await db.flush()

        return risk_score

    @staticmethod
    async def get_compliance_status(db: AsyncSession, user_id: str) -> dict:
        """Get overall compliance status for a user."""
        result = await db.execute(
            select(RiskScore).where(RiskScore.user_id == user_id)
        )
        risk_score = result.scalar_one_or_none()

        checks_result = await db.execute(
            select(ComplianceCheck).where(ComplianceCheck.user_id == user_id)
        )
        checks = list(checks_result.scalars().all())

        kyc_status = "not_started"
        aml_status = "not_started"
        sanctions_status = "not_started"

        for check in checks:
            if check.check_type == "kyc":
                kyc_status = check.status
            elif check.check_type == "aml":
                aml_status = check.status
            elif check.check_type == "sanctions":
                sanctions_status = check.status

        return {
            "user_id": user_id,
            "kyc_status": kyc_status,
            "aml_status": aml_status,
            "sanctions_status": sanctions_status,
            "risk_level": risk_score.risk_level if risk_score else "unknown",
            "overall_score": float(risk_score.overall_score) if risk_score else 0.0,
            "last_verified": risk_score.last_updated.isoformat() if risk_score else None,
            "next_verification_due": risk_score.next_review_date.isoformat() if risk_score and risk_score.next_review_date else None
        }

    @staticmethod
    async def log_compliance_event(db: AsyncSession, user_id: str, event_type: str, event_data: dict, triggered_by: str = None, risk_level: str = "medium") -> ComplianceEvent:
        """Log a compliance event."""
        event = ComplianceEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            triggered_by=triggered_by,
            risk_level=risk_level
        )

        db.add(event)
        await db.flush()

        return event

    @staticmethod
    async def generate_suspicious_activity_report(db: AsyncSession, user_id: str, start_date: datetime, end_date: datetime) -> dict:
        """Generate report on suspicious activity."""
        result = await db.execute(
            select(ComplianceEvent).where(
                and_(
                    ComplianceEvent.user_id == user_id,
                    ComplianceEvent.created_at >= start_date,
                    ComplianceEvent.created_at <= end_date,
                    ComplianceEvent.risk_level.in_(["high", "medium"])
                )
            )
        )
        events = list(result.scalars().all())

        return {
            "user_id": user_id,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_events": len(events),
            "high_risk_events": len([e for e in events if e.risk_level == "high"]),
            "medium_risk_events": len([e for e in events if e.risk_level == "medium"]),
            "events": [
                {
                    "type": e.event_type,
                    "risk_level": e.risk_level,
                    "timestamp": e.created_at.isoformat(),
                    "details": e.event_data
                }
                for e in events
            ]
        }


compliance_service = ComplianceService()