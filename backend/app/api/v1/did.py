"""Decentralized Identity API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.did_service import did_service
from app.schemas.common import (
    DIDCreateRequest, DIDCreateResponse,
    CredentialIssueRequest, CredentialVerifyRequest, CredentialVerifyResponse
)
from app.models.user import User


router = APIRouter()


@router.post("/create", response_model=DIDCreateResponse)
async def create_did(
    request: DIDCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new W3C DID for the current user."""
    try:
        did_response = await did_service.create_did(db, current_user, request.method, request.network)
        return did_response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resolve/{did}")
async def resolve_did(
    did: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a DID to its document."""
    resolution = await did_service.resolve_did(db, did)
    return resolution


@router.get("/document")
async def get_my_did_document(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's DID document."""
    if not current_user.did:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No DID found for user")

    document = await did_service.get_did_document(db, current_user.did)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DID document not found")

    return document


@router.post("/issue-credential")
async def issue_credential(
    request: CredentialIssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Issue a verifiable credential."""
    try:
        credential = await did_service.issue_credential(
            db, current_user, request.holder_did, request.credential_type, request.claims, request.expiration_date
        )
        return {"credential": credential}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-credential", response_model=CredentialVerifyResponse)
async def verify_credential(
    request: CredentialVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify a verifiable credential."""
    result = await did_service.verify_credential(db, request)
    return result


@router.post("/revoke-credential/{credential_id}")
async def revoke_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a verifiable credential."""
    success = await did_service.revoke_credential(db, credential_id, str(current_user.id))
    return {"revoked": success}


@router.post("/dao-membership")
async def create_dao_membership(
    dao_id: str,
    dao_name: str,
    holder_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a DAO membership credential."""
    from app.models.user import User as UserModel

    result = await db.execute(select(UserModel).where(UserModel.id == holder_id))
    holder = result.scalar_one_or_none()

    if not holder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holder not found")

    credential = await did_service.create_dao_membership_credential(db, current_user, holder, dao_id, dao_name)
    return {"credential": credential}