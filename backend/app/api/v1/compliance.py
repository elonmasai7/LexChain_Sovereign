"""Compliance and regulatory API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_compliance_officer, get_client_ip
from app.services.compliance_service import ComplianceService
from app.schemas.compliance import (
    AMLCheckRequest, KYCRequest, SanctionsScreeningRequest, WalletRiskRequest,
    ComplianceCheckResponse, RiskScoreResponse, ComplianceStatusResponse,
    ComplianceAlertRequest, ComplianceDashboardMetrics
)
from app.models.user import User


router = APIRouter()


@router.post("/aml", response_model=ComplianceCheckResponse)
async def run_aml_check(
    check_request: AMLCheckRequest,
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Run AML screening check."""
    check = await ComplianceService.run_aml_check(db, check_request)
    return check


@router.post("/kyc", response_model=ComplianceCheckResponse)
async def run_kyc(
    check_request: KYCRequest,
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Run KYC verification."""
    check = await ComplianceService.run_kyc(db, check_request)
    return check


@router.post("/sanctions", response_model=ComplianceCheckResponse)
async def run_sanctions_screening(
    check_request: SanctionsScreeningRequest,
    name: Optional[str] = None,
    wallet_address: Optional[str] = None,
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Run OFAC sanctions screening."""
    check = await ComplianceService.run_sanctions_screening(
        db, check_request, name, wallet_address
    )
    return check


@router.post("/wallet-risk", response_model=ComplianceCheckResponse)
async def analyze_wallet_risk(
    check_request: WalletRiskRequest,
    wallet_address: str,
    chain_id: int = 1,
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Analyze wallet risk score."""
    check = await ComplianceService.analyze_wallet_risk(
        db, check_request, wallet_address, chain_id
    )
    return check


@router.get("/status/{user_id}", response_model=ComplianceStatusResponse)
async def get_compliance_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overall compliance status for a user."""
    if current_user.role.value not in ["super_admin", "compliance_officer"] and str(current_user.id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    status = await ComplianceService.get_compliance_status(db, user_id)
    return ComplianceStatusResponse(**status)


@router.get("/risk-score/{user_id}", response_model=RiskScoreResponse)
async def get_risk_score(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get or generate risk score for a user."""
    if current_user.role.value not in ["super_admin", "compliance_officer"] and str(current_user.id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    risk_score = await ComplianceService.generate_risk_score(db, user_id)
    if not risk_score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No compliance data found")

    return risk_score


@router.get("/dashboard-metrics", response_model=ComplianceDashboardMetrics)
async def get_compliance_dashboard(
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Get compliance dashboard metrics."""
    from sqlalchemy import select, func
    from app.models.user import User
    from app.models.compliance import ComplianceCheck, SanctionHit, RiskScore

    total_users_result = await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None)))
    total_users = total_users_result.scalar() or 0

    verified_result = await db.execute(
        select(func.count(ComplianceCheck.id)).where(ComplianceCheck.status == "approved")
    )
    verified_users = verified_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(ComplianceCheck.id)).where(ComplianceCheck.status.in_(["pending", "in_review"]))
    )
    pending_verification = pending_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(ComplianceCheck.id)).where(ComplianceCheck.status == "rejected")
    )
    failed_verification = failed_result.scalar() or 0

    sanctions_result = await db.execute(select(func.count(SanctionHit.id)).where(SanctionHit.reviewed == False))
    sanctions_hits = sanctions_result.scalar() or 0

    high_risk_result = await db.execute(
        select(func.count(RiskScore.id)).where(RiskScore.risk_level == "high")
    )
    high_risk_users = high_risk_result.scalar() or 0

    medium_risk_result = await db.execute(
        select(func.count(RiskScore.id)).where(RiskScore.risk_level == "medium")
    )
    medium_risk_users = medium_risk_result.scalar() or 0

    low_risk_users = total_users - high_risk_users - medium_risk_users

    return ComplianceDashboardMetrics(
        total_users=total_users,
        verified_users=verified_users,
        pending_verification=pending_verification,
        failed_verification=failed_verification,
        sanctions_hits=sanctions_hits,
        high_risk_users=high_risk_users,
        medium_risk_users=medium_risk_users,
        low_risk_users=low_risk_users
    )


@router.post("/alert")
async def create_compliance_alert(
    alert_data: ComplianceAlertRequest,
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Create a compliance alert."""
    event = await ComplianceService.log_compliance_event(
        db,
        user_id=alert_data.user_id,
        event_type=alert_data.alert_type,
        event_data=alert_data.dict(),
        triggered_by=str(current_user.id),
        risk_level=alert_data.severity
    )
    return {"alert_id": str(event.id), "status": "created"}


@router.get("/events/{user_id}")
async def get_compliance_events(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Get compliance events for a user."""
    from datetime import datetime, timedelta
    from app.models.compliance import ComplianceEvent

    start = datetime.now(timezone.utc) - timedelta(days=30) if start_date is None else datetime.fromisoformat(start_date)
    end = datetime.now(timezone.utc) if end_date is None else datetime.fromisoformat(end_date)

    report = await ComplianceService.generate_suspicious_activity_report(db, user_id, start, end)
    return report