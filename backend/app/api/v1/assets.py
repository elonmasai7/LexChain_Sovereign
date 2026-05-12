"""Asset management API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_legal_officer, get_client_ip
from app.services.tokenization_service import TokenizationService
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetListResponse,
    TokenizationRequest, AssetVerificationRequest
)
from app.schemas.common import MessageResponse
from app.models.user import User


router = APIRouter()


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all assets with optional filters."""
    assets, total = await TokenizationService.list_assets(
        db, page, page_size, asset_type, status, jurisdiction
    )

    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset for tokenization."""
    try:
        asset = await TokenizationService.create_asset(db, asset_data, str(current_user.id))
        return asset
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get asset by ID."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    update_data: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update asset details."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    updated = await TokenizationService.update_asset(db, asset, update_data.model_dump(exclude_unset=True))
    return updated


@router.post("/{asset_id}/verify", response_model=AssetResponse)
async def verify_asset(
    asset_id: str,
    verification_data: AssetVerificationRequest,
    current_user: User = Depends(get_current_legal_officer),
    db: AsyncSession = Depends(get_db)
):
    """Submit asset for verification."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    verified = await TokenizationService.verify_asset(
        db, asset, verification_data.verification_type,
        verification_data.documents, verification_data.notes
    )
    return verified


@router.post("/{asset_id}/approve", response_model=AssetResponse)
async def approve_asset(
    asset_id: str,
    current_user: User = Depends(get_current_legal_officer),
    db: AsyncSession = Depends(get_db)
):
    """Approve a verified asset for tokenization."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    approved = await TokenizationService.approve_asset(db, asset, str(current_user.id))
    return approved


@router.post("/{asset_id}/tokenize", response_model=AssetResponse)
async def tokenize_asset(
    asset_id: str,
    tokenization_request: TokenizationRequest,
    current_user: User = Depends(get_current_legal_officer),
    db: AsyncSession = Depends(get_db)
):
    """Initiate asset tokenization."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    try:
        tokenized = await TokenizationService.mint_tokens(db, asset, tokenization_request, str(current_user.id))
        return tokenized
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{asset_id}/transfer", response_model=AssetResponse)
async def transfer_asset(
    asset_id: str,
    new_owner_id: str,
    current_user: User = Depends(get_current_legal_officer),
    db: AsyncSession = Depends(get_db)
):
    """Transfer asset ownership."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    transferred = await TokenizationService.transfer_ownership(
        db, asset, new_owner_id, str(current_user.id)
    )
    return transferred


@router.delete("/{asset_id}")
async def revoke_asset(
    asset_id: str,
    reason: str,
    current_user: User = Depends(get_current_legal_officer),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an asset tokenization."""
    asset = await TokenizationService.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    await TokenizationService.revoke_asset(db, asset, reason, str(current_user.id))
    return MessageResponse(message="Asset revoked successfully")


@router.get("/{asset_id}/analytics")
async def get_asset_analytics(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for an asset."""
    analytics = await TokenizationService.get_asset_analytics(db, asset_id)
    if not analytics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return analytics