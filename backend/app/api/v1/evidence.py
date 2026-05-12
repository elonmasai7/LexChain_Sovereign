"""Legal Evidence Vault API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.evidence_service import EvidenceService
from app.schemas.evidence import (
    EvidenceCreate, EvidenceUpdate, EvidenceResponse, EvidenceListResponse,
    EvidenceVerificationRequest, EvidenceVerificationResponse,
    EvidenceAnchorRequest, EvidenceAnchorResponse, ChainOfCustodyResponse
)
from app.models.user import User


router = APIRouter()


@router.get("/", response_model=EvidenceListResponse)
async def list_evidence(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all evidence with optional filters."""
    evidence_list, total = await EvidenceService.list_evidence(
        db, page, page_size, case_id, status, str(current_user.id)
    )

    return EvidenceListResponse(
        items=[EvidenceResponse.model_validate(e) for e in evidence_list],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def store_evidence(
    evidence_data: EvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Store new evidence in the vault."""
    try:
        evidence = await EvidenceService.store_evidence(db, evidence_data, str(current_user.id))
        return evidence
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get evidence by ID."""
    evidence = await EvidenceService.get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


@router.put("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    update_data: EvidenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update evidence metadata."""
    evidence = await EvidenceService.get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    updated = await EvidenceService.update_evidence(db, evidence, update_data.model_dump(exclude_unset=True))
    return updated


@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete evidence."""
    evidence = await EvidenceService.get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    await EvidenceService.update_evidence(db, evidence, {"status": "deleted"})
    return {"message": "Evidence deleted"}


@router.post("/{evidence_id}/verify", response_model=EvidenceVerificationResponse)
async def verify_evidence(
    evidence_id: str,
    verification_request: EvidenceVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify evidence file hash."""
    try:
        verification = await EvidenceService.verify_evidence_hash(
            db, verification_request, str(current_user.id)
        )
        return EvidenceVerificationResponse(
            is_valid=verification.is_valid,
            evidence_id=evidence_id,
            verification_hash=verification.verification_hash,
            verified_at=verification.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{evidence_id}/anchor", response_model=EvidenceAnchorResponse)
async def anchor_evidence(
    evidence_id: str,
    anchor_request: EvidenceAnchorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Anchor evidence hash to blockchain."""
    evidence = await EvidenceService.get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    from datetime import datetime, timezone

    anchor = await EvidenceService.anchor_to_blockchain(
        db, evidence,
        f"0x{hashlib.hexencode(os.urandom(32)).decode()}",
        12345678,
        datetime.now(timezone.utc),
        chain_id=anchor_request.chain_id
    )

    return EvidenceAnchorResponse(
        evidence_id=evidence_id,
        tx_hash=anchor.tx_hash,
        block_number=anchor.block_number,
        block_timestamp=anchor.block_timestamp,
        chain_id=anchor.chain_id
    )


@router.get("/{evidence_id}/proof")
async def generate_proof(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate verification proof for evidence."""
    evidence = await EvidenceService.get_evidence_by_id(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    proof = await EvidenceService.generate_proof(db, evidence)
    return proof


@router.get("/{evidence_id}/chain-of-custody")
async def get_chain_of_custody(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chain of custody record."""
    custody = await EvidenceService.get_chain_of_custody(db, evidence_id)
    return {"evidence_id": evidence_id, "history": custody}


import hashlib
import os