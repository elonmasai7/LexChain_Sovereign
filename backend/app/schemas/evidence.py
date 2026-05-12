"""Evidence-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EvidenceCreate(BaseModel):
    """Schema for creating evidence."""
    case_id: Optional[str] = Field(None, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    ipfs_cid: Optional[str] = None
    chain_id: Optional[int] = 1
    metadata: Optional[dict] = {}
    tags: Optional[list[str]] = []


class EvidenceUpdate(BaseModel):
    """Schema for updating evidence."""
    case_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict] = None


class EvidenceResponse(BaseModel):
    """Evidence response schema."""
    id: str
    case_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: str
    ipfs_cid: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    chain_id: Optional[int] = None
    status: str
    uploaded_by: Optional[str] = None
    verification_count: int
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    """Paginated evidence list."""
    items: list[EvidenceResponse]
    total: int
    page: int
    page_size: int


class EvidenceVerificationRequest(BaseModel):
    """Request to verify evidence."""
    evidence_id: str
    file_content_hash: str


class EvidenceVerificationResponse(BaseModel):
    """Evidence verification response."""
    is_valid: bool
    evidence_id: str
    verification_hash: str
    blockchain_proof: Optional[dict] = None
    verified_at: datetime


class EvidenceAnchorRequest(BaseModel):
    """Request to anchor evidence to blockchain."""
    evidence_id: str
    chain_id: int = 1


class EvidenceAnchorResponse(BaseModel):
    """Evidence anchoring response."""
    evidence_id: str
    tx_hash: str
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None
    chain_id: int


class ChainOfCustodyResponse(BaseModel):
    """Chain of custody record."""
    evidence_id: str
    history: list[dict]