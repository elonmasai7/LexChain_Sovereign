"""Common Pydantic schemas."""
from datetime import datetime
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    uptime: float
    database: str
    redis: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class ListResponse(BaseModel, Generic[T]):
    """Generic list response."""
    items: list[T]
    count: int


class SuccessResponse(BaseModel):
    """Success response with data."""
    success: bool = True
    data: Optional[dict] = None
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchParams(BaseModel):
    """Search parameters."""
    query: Optional[str] = None
    filters: Optional[dict] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AuditLogResponse(BaseModel):
    """Audit log response."""
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: dict
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    """Audit log query parameters."""
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class DIDCreateRequest(BaseModel):
    """DID creation request."""
    method: str = "ethr"
    network: str = "mainnet"


class DIDCreateResponse(BaseModel):
    """DID creation response."""
    did: str
    did_document: dict
    private_key: Optional[str] = None


class CredentialIssueRequest(BaseModel):
    """Credential issuance request."""
    issuer_did: str
    holder_did: str
    credential_type: str
    claims: dict
    expiration_date: Optional[datetime] = None


class CredentialVerifyRequest(BaseModel):
    """Credential verification request."""
    credential: dict


class CredentialVerifyResponse(BaseModel):
    """Credential verification response."""
    is_valid: bool
    issuer: Optional[str] = None
    holder: Optional[str] = None
    claims: Optional[dict] = None
    errors: Optional[list[str]] = None