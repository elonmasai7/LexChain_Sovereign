"""Analytics and dashboard Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    """Dashboard metrics response."""
    total_users: int
    active_users: int
    total_assets: int
    asset_value_usd: float
    total_documents: int
    pending_signatures: int
    compliance_score: float
    risk_score: float
    active_proposals: int
    governance_participation: float
    recent_activity: list[dict]


class ComplianceMetrics(BaseModel):
    """Compliance metrics."""
    total_verifications: int
    verified_users: int
    pending_verifications: int
    failed_verifications: int
    sanctions_hits: int
    risk_distribution: dict
    verification_by_type: dict
    trend_data: list[dict]


class AssetDistribution(BaseModel):
    """Asset distribution metrics."""
    by_type: dict
    by_jurisdiction: dict
    by_status: dict
    total_value_by_type: dict
    top_assets: list[dict]
    recent_tokenizations: list[dict]


class GovernanceActivity(BaseModel):
    """Governance activity metrics."""
    total_proposals: int
    active_proposals: int
    passed_proposals: int
    failed_proposals: int
    total_votes: int
    unique_voters: int
    avg_turnout: float
    voting_power_distribution: dict
    recent_proposals: list[dict]


class RegulatoryAlert(BaseModel):
    """Regulatory alert."""
    id: str
    alert_type: str
    severity: str
    title: str
    description: str
    affected_users: Optional[int] = None
    action_required: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None


class AIUsageMetrics(BaseModel):
    """AI service usage metrics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    tokens_used: int
    cost_usd: float
    by_operation_type: dict


class SystemHealthMetrics(BaseModel):
    """System health metrics."""
    uptime_seconds: int
    avg_response_time_ms: float
    error_rate: float
    db_connection_pool: dict
    redis_connection_pool: dict
    active_sessions: int
    queue_depth: dict