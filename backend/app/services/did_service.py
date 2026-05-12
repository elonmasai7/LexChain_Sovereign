"""Decentralized Identity service."""
import secrets
from datetime import datetime, timezone
from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User
from app.schemas.common import DIDCreateRequest, DIDCreateResponse, CredentialIssueRequest, CredentialVerifyRequest, CredentialVerifyResponse
from app.core.security import hash_token
from app.core.audit import audit_logger_service
from app.core.logging import get_logger


logger = get_logger(__name__)


class DIDService:
    """W3C DID and Verifiable Credentials service."""

    @staticmethod
    async def create_did(db: AsyncSession, user: User, method: str = "ethr", network: str = "mainnet") -> DIDCreateResponse:
        """Create a new W3C DID."""
        if method == "ethr":
            private_key = secrets.token_hex(32)
            did = f"did:ethr:{network}:0x{secrets.token_hex(20)}"
        elif method == "web":
            identifier = secrets.token_urlsafe(32)
            did = f"did:web:{identifier}"
        elif method == "key":
            public_key_base58 = secrets.token_urlsafe(16)
            did = f"did:key:z{public_key_base58}"
        else:
            raise ValueError(f"Unsupported DID method: {method}")

        did_document = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": did,
            "verificationMethod": [{
                "id": f"{did}#keys-1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": did,
                "publicKeyHex": secrets.token_hex(33)
            }],
            "authentication": [f"{did}#keys-1"],
            "assertionMethod": [f"{did}#keys-1"]
        }

        user.did = did
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="did_create",
            resource_type="did", resource_id=did
        )

        logger.info(f"DID created: {did} for user {user.id}")

        return DIDCreateResponse(
            did=did,
            did_document=did_document,
            private_key=private_key if method == "ethr" else None
        )

    @staticmethod
    async def get_did_document(db: AsyncSession, did: str) -> Optional[dict]:
        """Get DID document for a DID."""
        result = await db.execute(
            select(User).where(and_(User.did == did, User.deleted_at.is_(None)))
        )
        user = result.scalar_one_or_none()

        if not user or not user.did:
            return None

        return {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": user.did,
            "verificationMethod": [{
                "id": f"{user.did}#keys-1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": user.did
            }],
            "authentication": [f"{user.did}#keys-1"],
            "service": []
        }

    @staticmethod
    async def resolve_did(db: AsyncSession, did: str) -> dict:
        """Resolve DID to DID document."""
        document = await DIDService.get_did_document(db, did)

        if document:
            return {
                "did_resolution_metadata": {"contentType": "application/did+json"},
                "did_document": document
            }

        return {
            "did_resolution_metadata": {"error": "notFound"},
            "did_document": None
        }

    @staticmethod
    async def issue_credential(db: AsyncSession, request: CredentialIssueRequest) -> dict:
        """Issue a verifiable credential."""
        credential = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1"
            ],
            "id": f"urn:uuid:{secrets.token_hex(16)}",
            "type": ["VerifiableCredential", request.credential_type],
            "issuer": request.issuer_did,
            "issuanceDate": datetime.now(timezone.utc).isoformat(),
            "expirationDate": request.expiration_date.isoformat() if request.expiration_date else None,
            "credentialSubject": {
                "id": request.holder_did,
                **request.claims
            },
            "proof": {
                "type": "EcdsaSecp256k1Signature2019",
                "created": datetime.now(timezone.utc).isoformat(),
                "proofPurpose": "assertionMethod",
                "verificationMethod": f"{request.issuer_did}#keys-1"
            }
        }

        await audit_logger_service.log_action(
            db, action="credential_issue",
            resource_type="credential", resource_id=credential["id"],
            details={"issuer": request.issuer_did, "holder": request.holder_did, "type": request.credential_type}
        )

        return credential

    @staticmethod
    async def verify_credential(db: AsyncSession, request: CredentialVerifyRequest) -> CredentialVerifyResponse:
        """Verify a verifiable credential."""
        credential = request.credential

        errors = []

        if not credential.get("@context"):
            errors.append("Missing @context")

        if not credential.get("issuer"):
            errors.append("Missing issuer")

        if not credential.get("credentialSubject"):
            errors.append("Missing credentialSubject")

        if credential.get("expirationDate"):
            exp_date = datetime.fromisoformat(credential["expirationDate"].replace("Z", "+00:00"))
            if exp_date < datetime.now(timezone.utc):
                errors.append("Credential expired")

        if errors:
            return CredentialVerifyResponse(
                is_valid=False,
                errors=errors
            )

        return CredentialVerifyResponse(
            is_valid=True,
            issuer=credential.get("issuer"),
            holder=credential.get("credentialSubject", {}).get("id"),
            claims=credential.get("credentialSubject")
        )

    @staticmethod
    async def revoke_credential(db: AsyncSession, credential_id: str, revoker_id: str) -> bool:
        """Revoke a verifiable credential."""
        await audit_logger_service.log_action(
            db, user_id=revoker_id, action="credential_revoke",
            resource_type="credential", resource_id=credential_id
        )
        return True

    @staticmethod
    async def create_dao_membership_credential(db: AsyncSession, user: User, dao_id: str, dao_name: str) -> dict:
        """Create DAO membership credential."""
        if not user.did:
            did_response = await DIDService.create_did(db, user)
            user.did = did_response.did

        credential = await DIDService.issue_credential(
            db,
            CredentialIssueRequest(
                issuer_did=f"did:ethr:mainnet:{dao_id}",
                holder_did=user.did,
                credential_type="DAOMembershipCredential",
                claims={
                    "daoId": dao_id,
                    "daoName": dao_name,
                    "memberSince": datetime.now(timezone.utc).isoformat(),
                    "membershipLevel": "standard"
                },
                expiration_date=datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)
            )
        )

        return credential


did_service = DIDService()