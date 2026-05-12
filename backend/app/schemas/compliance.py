"""Compliance-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ComplianceCheckRequest(BaseModel):
    """Base compliance check request."""
    user_id: str
    check_type: str = Field(..., description="aml, kyc, sanctions, wallet_risk")
    provider: Optional[str] = None


class AMLCheckRequest(ComplianceCheckRequest):
    """AML screening request."""
    check_type: str = "aml"
    transaction_data: Optional[dict] = None


class KYCRequest(ComplianceCheckRequest):
    """KYC verification request."""
    check_type: str = "kyc"
    verification_data: Optional[dict] = None


class SanctionsScreeningRequest(ComplianceCheckRequest):
    """Sanctions screening request."""
    check_type: str = "sanctions"
    name: Optional[str] = None
    wallet_address: Optional[str] = None


class WalletRiskRequest(ComplianceCheckRequest):
    """Wallet risk analysis request."""
    check_type: str = "wallet_risk"
    wallet_address: str
    chain_id: Optional[int] = 1


class ComplianceCheckResponse(BaseModel):
    """Compliance check response."""
    id: str
    user_id: str
    check_type: str
    status: str
    result: Optional[dict] = None
    provider: Optional[str] = None
    score: Optional[float] = None
    risk_level: Optional[str] = None
    checked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RiskScoreResponse(BaseModel):
    """User risk score response."""
    user_id: str
    overall_score: float = Field(..., ge=0, le=100)
    risk_level: str
    category_scores: dict
    risk_factors: list[dict]
    recommendations: list[str]
    last_updated: datetime

    model_config = {"from_attributes": True}


class SanctionHitResponse(BaseModel):
    """Sanction hit response."""
    id: str
    user_id: str
    list_name: str
    matched_name: str
    matched_id: Optional[str] = None
    match_score: Optional[float] = None
    risk_level: str
    reviewed: bool
    false_positive: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceStatusResponse(BaseModel):
    """Overall compliance status."""
    user_id: str
    kyc_status: str
    aml_status: str
    sanctions_status: str
    risk_level: str
    overall_score: float
    last_verified: Optional[datetime] = None
    next_verification_due: Optional[datetime] = None


class ComplianceDashboardMetrics(BaseModel):
    """Compliance dashboard metrics."""
    total_users: int
    verified_users: int
    pending_verification: int
    failed_verification: int
    sanctions_hits: int
    high_risk_users: int
    medium_risk_users: int
    low_risk_users: int


class ComplianceAlertRequest(BaseModel):
    """Create compliance alert."""
    user_id: Optional[str] = None
    alert_type: str
    severity: str
    description: str
    metadata: Optional[dict] = None