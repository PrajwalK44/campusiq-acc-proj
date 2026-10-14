import os
import shutil
import uuid
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.core.security import get_current_user, require_role
from backend.app.models.entities import User, Document
from backend.app.schemas.api_models import DocumentResponse
from backend.app.rag.extractor import PDFExtractor, TextSplitter
from backend.app.rag.vector_store import EmbeddingService, VectorStoreService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents & Ingestion"])

embedding_service = EmbeddingService.get_instance()
vector_store = VectorStoreService.get_instance()


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all registered and indexed institutional documents."""
    docs = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_index_document(
    title: str = Form(...),
    category: str = Form("General"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Admin-only: Upload a PDF document, extract text, compute embeddings,
    index into ChromaDB, and record metadata in Supabase.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    content_hash = PDFExtractor.calculate_file_hash(file_path)

    # Register document in Supabase
    doc_record = Document(
        title=title,
        original_filename=file.filename,
        category=category,
        uploaded_by=current_user.id,
        processing_status="PROCESSING",
        content_hash=content_hash,
        chunk_count=0
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    try:
        pages_data = PDFExtractor.extract_text_with_pages(file_path)
        if not pages_data:
            raise ValueError("No extractable text found in PDF document (may be scanned or empty).")

        chunks = TextSplitter.split_into_chunks(
            pages_data,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.encode(chunk_texts)

        chunk_ids = [f"{doc_record.id}_{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "document_id": str(doc_record.id),
                "title": doc_record.title,
                "category": doc_record.category,
                "page_number": c["page_number"]
            }
            for c in chunks
        ]

        # Index in ChromaDB
        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas
        )

        doc_record.processing_status = "INDEXED"
        doc_record.chunk_count = len(chunks)
        db.commit()
        db.refresh(doc_record)
        return DocumentResponse.model_validate(doc_record)

    except Exception as e:
        logger.error(f"Document ingestion failed for {file.filename}: {e}")
        doc_record.processing_status = "FAILED"
        doc_record.error_details = str(e)
        db.commit()
        db.refresh(doc_record)
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(e)}")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Admin-only: Remove document metadata from Supabase and delete vectors from ChromaDB."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Clean up ChromaDB chunks
    try:
        vector_store.delete_document_chunks(str(document_id))
    except Exception as e:
        logger.warning(f"Error purging vectors for {document_id}: {e}")

    db.delete(doc)
    db.commit()
    return None


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Admin-only: Re-run chunking and vector indexing for an existing document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Find file in upload dir
    matching_files = [f for f in os.listdir(settings.UPLOAD_DIR) if doc.original_filename in f]
    if not matching_files:
        raise HTTPException(status_code=404, detail="Source PDF file not found on disk")

    file_path = os.path.join(settings.UPLOAD_DIR, matching_files[0])

    try:
        vector_store.delete_document_chunks(str(doc.id))
        pages_data = PDFExtractor.extract_text_with_pages(file_path)
        chunks = TextSplitter.split_into_chunks(pages_data, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.encode(chunk_texts)

        chunk_ids = [f"{doc.id}_{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "document_id": str(doc.id),
                "title": doc.title,
                "category": doc.category,
                "page_number": c["page_number"]
            }
            for c in chunks
        ]

        vector_store.add_chunks(chunk_ids, embeddings, chunk_texts, metadatas)
        doc.processing_status = "INDEXED"
        doc.chunk_count = len(chunks)
        doc.version += 1
        db.commit()
        db.refresh(doc)
        return DocumentResponse.model_validate(doc)
    except Exception as e:
        doc.processing_status = "FAILED"
        doc.error_details = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")
