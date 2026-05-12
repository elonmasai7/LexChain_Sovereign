"""Asset-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.core.validation import InputValidator


class AssetCreate(BaseModel):
    """Schema for creating a new asset."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: str = Field(..., description="real_estate, carbon_credit, agriculture, art, commodity")
    jurisdiction: Optional[str] = Field(None, max_length=100)
    total_supply: Optional[Decimal] = None
    fractional: bool = False
    custodian: Optional[str] = Field(None, max_length=255)
    valuation: Optional[Decimal] = None
    currency: str = "USD"
    legal_metadata: Optional[dict] = {}
    compliance_rules: Optional[dict] = {}

    @field_validator('asset_type')
    @classmethod
    def validate_asset_type(cls, v):
        valid_types = ['real_estate', 'carbon_credit', 'agriculture', 'art', 'commodity']
        if v not in valid_types:
            raise ValueError(f"Asset type must be one of: {valid_types}")
        return v


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    custodian: Optional[str] = Field(None, max_length=255)
    valuation: Optional[Decimal] = None
    legal_metadata: Optional[dict] = None
    compliance_rules: Optional[dict] = None


class AssetResponse(BaseModel):
    """Asset response schema."""
    id: str
    name: str
    description: Optional[str] = None
    asset_type: str
    jurisdiction: Optional[str] = None
    owner_id: Optional[str] = None
    token_id: Optional[str] = None
    contract_address: Optional[str] = None
    chain_id: Optional[int] = None
    total_supply: Optional[str] = None
    fractional: bool
    verification_status: str
    custodian: Optional[str] = None
    valuation: Optional[str] = None
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetListResponse(BaseModel):
    """Paginated asset list response."""
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TokenizationRequest(BaseModel):
    """Request to tokenize an asset."""
    asset_id: str
    chain_id: int = Field(..., description="Blockchain network ID (1=mainnet, 137=polygon, etc.)")
    initial_supply: Optional[Decimal] = None
    transfer_restrictions: bool = True
    compliance_enabled: bool = True


class AssetVerificationRequest(BaseModel):
    """Request to verify an asset."""
    verification_type: str = Field(..., description="ownership, valuation, legal, compliance")
    documents: Optional[list[str]] = None
    notes: Optional[str] = None


class AssetSearchRequest(BaseModel):
    """Asset search parameters."""
    query: Optional[str] = None
    asset_type: Optional[str] = None
    status: Optional[str] = None
    jurisdiction: Optional[str] = None
    min_valuation: Optional[Decimal] = None
    max_valuation: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)