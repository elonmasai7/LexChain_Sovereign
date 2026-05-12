"""Analytics and Dashboard API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_compliance_officer
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    DashboardMetrics, ComplianceMetrics, AssetDistribution,
    GovernanceActivity, RegulatoryAlert
)
from app.models.user import User


router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get main dashboard metrics."""
    metrics = await AnalyticsService.get_dashboard_metrics(db)
    return metrics


@router.get("/compliance", response_model=ComplianceMetrics)
async def get_compliance_metrics(
    current_user: User = Depends(get_current_compliance_officer),
    db: AsyncSession = Depends(get_db)
):
    """Get compliance metrics."""
    metrics = await AnalyticsService.get_compliance_metrics(db)
    return metrics


@router.get("/assets", response_model=AssetDistribution)
async def get_asset_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get asset distribution metrics."""
    distribution = await AnalyticsService.get_asset_distribution(db)
    return distribution


@router.get("/governance", response_model=GovernanceActivity)
async def get_governance_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get governance activity metrics."""
    activity = await AnalyticsService.get_governance_activity(db)
    return activity


@router.get("/regulatory-alerts")
async def get_regulatory_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active regulatory alerts."""
    alerts = await AnalyticsService.get_regulatory_alerts(db)
    return {"alerts": alerts, "total": len(alerts)}