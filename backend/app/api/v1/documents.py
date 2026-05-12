"""Document management API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_client_ip
from app.services.document_service import DocumentService
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse,
    ContractAnalysisRequest, ContractAnalysisResponse, DocumentSignRequest
)
from app.schemas.common import MessageResponse
from app.models.user import User


router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents with optional filters."""
    documents, total = await DocumentService.list_documents(
        db, page, page_size, document_type, status, str(current_user.id)
    )

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new legal document."""
    try:
        document = await DocumentService.create_document(db, doc_data, str(current_user.id))
        return document
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document by ID."""
    document = await DocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a document."""
    document = await DocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    updated = await DocumentService.update_document(db, document, update_data.model_dump(exclude_unset=True))
    return updated


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document (soft delete)."""
    document = await DocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await DocumentService.delete_document(db, document)
    return MessageResponse(message="Document deleted successfully")


@router.post("/{document_id}/sign")
async def sign_document(
    document_id: str,
    signature_data: DocumentSignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sign a document."""
    document = await DocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    signature = await DocumentService.sign_document(
        db, document, str(current_user.id),
        signature_data.model_dump(), get_client_ip(request)
    )

    return {
        "signature_id": str(signature.id),
        "signature_hash": signature.signature_hash,
        "signed_at": signature.signed_at.isoformat()
    }


@router.post("/{document_id}/anchor")
async def anchor_document(
    document_id: str,
    tx_hash: str,
    chain_id: int = 1,
    ipfs_hash: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Anchor document hash to blockchain."""
    document = await DocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await DocumentService.anchor_to_blockchain(db, document, tx_hash, chain_id, ipfs_hash)

    return {
        "document_hash": document.document_hash,
        "tx_hash": tx_hash,
        "chain_id": chain_id,
        "ipfs_hash": ipfs_hash
    }


@router.get("/{document_id}/history")
async def get_document_history(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document version history."""
    history = await DocumentService.get_document_history(db, document_id)
    return [DocumentResponse.model_validate(d) for d in history]


@router.get("/{document_id}/export/pdf")
async def export_document_pdf(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export document as PDF."""
    pdf_content = await DocumentService.export_pdf(db, document_id)

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=document_{document_id}.pdf"}
    )


@router.get("/{document_id}/verify/{tx_hash}")
async def verify_document(
    document_id: str,
    tx_hash: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify document against on-chain record."""
    document = await DocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    is_valid = await DocumentService.verify_blockchain_proof(db, document, tx_hash)

    return {
        "is_valid": is_valid,
        "document_hash": document.document_hash,
        "submitted_tx": tx_hash,
        "anchored_tx": document.blockchain_tx_hash
    }