"""Document-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Schema for creating a legal document."""
    title: str = Field(..., min_length=1, max_length=255)
    document_type: str = Field(..., description="nda, investment_agreement, token_purchase, etc.")
    jurisdiction: Optional[str] = Field(None, max_length=100)
    content: Optional[dict] = {}
    clauses: Optional[list[dict]] = []
    parties: Optional[list[dict]] = []
    template_id: Optional[str] = None
    metadata: Optional[dict] = {}


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[dict] = None
    clauses: Optional[list[dict]] = None
    parties: Optional[list[dict]] = None
    metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    title: str
    document_type: str
    jurisdiction: Optional[str] = None
    status: str
    version: str
    ipfs_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    chain_id: Optional[int] = None
    document_hash: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated document list."""
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentSignatureRequest(BaseModel):
    """Request to sign a document."""
    document_id: str
    signature_data: Optional[dict] = None
    sign_with_wallet: bool = False


class DocumentSignRequest(BaseModel):
    """Request to add signature to document."""
    signature_hash: str
    signature_data: Optional[dict] = None


class ContractAnalysisRequest(BaseModel):
    """Request to analyze a contract."""
    contract_text: str = Field(..., min_length=10)
    contract_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    analyze_risks: bool = True
    extract_clauses: bool = True


class ContractAnalysisResponse(BaseModel):
    """Contract analysis results."""
    summary: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_factors: list[dict]
    clauses: list[dict]
    compliance_score: float = Field(..., ge=0, le=100)
    recommendations: list[str]
    jurisdiction_comparison: Optional[dict] = None


class ClauseExtractionRequest(BaseModel):
    """Request to extract clauses from document."""
    document_text: str
    clause_types: Optional[list[str]] = None


class ClauseExtractionResponse(BaseModel):
    """Clause extraction results."""
    clauses: list[dict]
    total_count: int
    categories: dict


class JurisdictionComparisonRequest(BaseModel):
    """Request to compare jurisdictions."""
    contract_text: str
    jurisdictions: list[str]


class DocumentAnchorRequest(BaseModel):
    """Request to anchor document hash to blockchain."""
    document_id: str
    chain_id: int = 1


class DocumentExportRequest(BaseModel):
    """Request to export document."""
    document_id: str
    format: str = "pdf"
    include_signatures: bool = True
    include_blockchain_proof: bool = True