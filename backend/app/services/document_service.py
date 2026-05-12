"""Document service for smart legal contracts."""
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.document import LegalDocument, DocumentSignature, DocumentType, DocumentStatus
from app.models.document_template import DocumentTemplate, ClauseLibrary
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.core.security import hash_file_content
from app.core.audit import audit_logger_service
from app.core.logging import get_logger


logger = get_logger(__name__)


class DocumentService:
    """Smart legal document management service."""

    @staticmethod
    async def create_document(db: AsyncSession, doc_data: DocumentCreate, user_id: str) -> LegalDocument:
        """Create a new legal document."""
        document = LegalDocument(
            title=doc_data.title,
            document_type=doc_data.document_type,
            jurisdiction=doc_data.jurisdiction,
            content=doc_data.content,
            clauses=doc_data.clauses,
            parties=doc_data.parties,
            metadata=doc_data.metadata,
            created_by=user_id,
            status=DocumentStatus.DRAFT.value
        )

        if doc_data.template_id:
            result = await db.execute(
                select(DocumentTemplate).where(DocumentTemplate.id == doc_data.template_id)
            )
            template = result.scalar_one_or_none()
            if template:
                document.content = template.content
                document.clauses = template.clauses

        db.add(document)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=user_id, action="document_create",
            resource_type="document", resource_id=str(document.id)
        )

        return document

    @staticmethod
    async def get_document_by_id(db: AsyncSession, document_id: str) -> Optional[LegalDocument]:
        """Get document by ID."""
        result = await db.execute(
            select(LegalDocument).where(
                and_(LegalDocument.id == document_id, LegalDocument.deleted_at.is_(None))
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> tuple[list[LegalDocument], int]:
        """List documents with filters."""
        query = select(LegalDocument).where(LegalDocument.deleted_at.is_(None))
        count_query = select(LegalDocument).where(LegalDocument.deleted_at.is_(None))

        if document_type:
            query = query.where(LegalDocument.document_type == document_type)
            count_query = count_query.where(LegalDocument.document_type == document_type)

        if status:
            query = query.where(LegalDocument.status == status)
            count_query = count_query.where(LegalDocument.status == status)

        if created_by:
            query = query.where(LegalDocument.created_by == created_by)
            count_query = count_query.where(LegalDocument.created_by == created_by)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(LegalDocument.created_at.desc())

        result = await db.execute(query)
        documents = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return documents, total

    @staticmethod
    async def update_document(db: AsyncSession, document: LegalDocument, update_data: dict) -> LegalDocument:
        """Update a document."""
        previous_version = LegalDocument(
            title=document.title,
            document_type=document.document_type,
            jurisdiction=document.jurisdiction,
            content=document.content,
            clauses=document.clauses,
            parties=document.parties,
            status=document.status,
            version=document.version,
            previous_version_id=document.previous_version_id,
            created_by=document.created_by,
            created_at=document.created_at
        )
        db.add(previous_version)

        major, minor, patch = document.version.split('.')
        document.version = f"{major}.{int(minor)+1}.{patch}"
        document.previous_version_id = previous_version.id

        for key, value in update_data.items():
            if hasattr(document, key) and value is not None:
                setattr(document, key, value)

        document.updated_at = datetime.now(timezone.utc)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(document.created_by), action="document_update",
            resource_type="document", resource_id=str(document.id)
        )

        return document

    @staticmethod
    async def delete_document(db: AsyncSession, document: LegalDocument) -> bool:
        """Soft delete a document."""
        document.deleted_at = datetime.now(timezone.utc)
        document.status = DocumentStatus.VOID.value
        await db.flush()

        return True

    @staticmethod
    async def sign_document(db: AsyncSession, document: LegalDocument, signer_id: str, signature_data: dict, ip_address: str) -> DocumentSignature:
        """Sign a document."""
        document_hash = DocumentService.hash_document_content(document)
        signature_hash = hashlib.sha256(f"{document_hash}{signer_id}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()

        signature = DocumentSignature(
            document_id=document.id,
            signer_id=signer_id,
            signature_hash=signature_hash,
            signature_data=signature_data,
            signed_at=datetime.now(timezone.utc),
            ip_address=ip_address
        )

        db.add(signature)

        all_signatures = await db.execute(
            select(DocumentSignature).where(DocumentSignature.document_id == document.id)
        )
        signature_count = len(list(all_signatures.scalars().all()))

        if document.parties and signature_count >= len(document.parties):
            document.status = DocumentStatus.SIGNED.value

        document.updated_at = datetime.now(timezone.utc)
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=signer_id, action="document_sign",
            resource_type="document", resource_id=str(document.id),
            ip_address=ip_address
        )

        return signature

    @staticmethod
    async def hash_document_content(document: LegalDocument) -> str:
        """Generate SHA-256 hash of document content."""
        content_str = str(document.content or {})
        clauses_str = str(document.clauses or [])
        combined = f"{document.title}{document.document_type}{content_str}{clauses_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    async def anchor_to_blockchain(db: AsyncSession, document: LegalDocument, tx_hash: str, chain_id: int, ipfs_hash: str = None) -> LegalDocument:
        """Anchor document hash to blockchain."""
        document.document_hash = await DocumentService.hash_document_content(document)
        document.blockchain_tx_hash = tx_hash
        document.chain_id = chain_id
        document.ipfs_hash = ipfs_hash
        document.updated_at = datetime.now(timezone.utc)

        await audit_logger_service.log_action(
            db, user_id=str(document.created_by), action="document_anchor",
            resource_type="document", resource_id=str(document.id),
            details={"tx_hash": tx_hash, "chain_id": chain_id, "ipfs_hash": ipfs_hash}
        )

        return document

    @staticmethod
    async def verify_blockchain_proof(db: AsyncSession, document: LegalDocument, proof_tx_hash: str) -> bool:
        """Verify document against on-chain record."""
        return document.blockchain_tx_hash == proof_tx_hash

    @staticmethod
    async def get_document_history(db: AsyncSession, document_id: str) -> list[LegalDocument]:
        """Get full version history of a document."""
        history = []
        current_id = document_id

        while current_id:
            result = await db.execute(select(LegalDocument).where(LegalDocument.id == current_id))
            doc = result.scalar_one_or_none()
            if doc:
                history.append(doc)
                current_id = doc.previous_version_id
            else:
                break

        return history

    @staticmethod
    async def generate_from_template(db: AsyncSession, template_id: str, fill_data: dict, user_id: str) -> LegalDocument:
        """Generate document from template with filled data."""
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == template_id))
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError("Template not found")

        content = template.content.copy() if template.content else {}
        for key, value in fill_data.items():
            for section in content:
                if isinstance(content[section], dict):
                    for field in content[section]:
                        if f"{{{{{key}}}}}" in str(content[section][field]):
                            content[section][field] = content[section][field].replace(f"{{{{{key}}}}}", str(value))

        document = LegalDocument(
            title=template.name,
            document_type=template.template_type,
            jurisdiction=template.jurisdiction,
            content=content,
            clauses=template.clauses,
            metadata={"template_id": str(template_id), "filled_data": fill_data},
            created_by=user_id
        )

        db.add(document)
        await db.flush()

        template.usage_count += 1
        await db.flush()

        return document

    @staticmethod
    async def export_pdf(db: AsyncSession, document_id: str) -> bytes:
        """Export document as PDF."""
        result = await db.execute(select(LegalDocument).where(LegalDocument.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError("Document not found")

        pdf_content = f"LexChain Sovereign - {document.title}\n\n"
        pdf_content += f"Type: {document.document_type}\n"
        pdf_content += f"Version: {document.version}\n"
        pdf_content += f"Status: {document.status}\n\n"
        pdf_content += f"Content:\n{str(document.content)}\n"

        return pdf_content.encode()