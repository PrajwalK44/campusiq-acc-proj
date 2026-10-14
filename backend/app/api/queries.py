from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.security import get_current_user
from backend.app.models.entities import User, QueryHistory, QuerySource, Feedback
from backend.app.schemas.api_models import (
    QueryRequest,
    QueryResponse,
    QuerySourceResponse,
    FeedbackRequest,
    FeedbackResponse
)
from backend.app.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/queries", tags=["Queries & RAG"])
rag_pipeline = RAGPipeline()


@router.post("", response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
def submit_student_query(
    query_in: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a college-related query. Performs real RAG over indexed documents,
    records citations in Supabase, and logs user query history.
    """
    answer_text, answer_status, valid_sources = rag_pipeline.answer_student_query(
        question=query_in.question,
        category=query_in.category or "General"
    )

    # Persist in Supabase
    new_query = QueryHistory(
        user_id=current_user.id,
        question=query_in.question,
        answer=answer_text,
        category=query_in.category or "General",
        answer_status=answer_status
    )
    db.add(new_query)
    db.flush()

    source_responses = []
    for src in valid_sources:
        doc_uuid = UUID(src["document_id"]) if src.get("document_id") else None
        db_source = QuerySource(
            query_id=new_query.id,
            document_id=doc_uuid,
            chunk_id=src["chunk_id"],
            document_title=src["title"],
            page_number=src.get("page_number"),
            excerpt=src["text"]
        )
        db.add(db_source)
        source_responses.append(QuerySourceResponse(
            chunk_id=src["chunk_id"],
            document_id=doc_uuid,
            document_title=src["title"],
            page_number=src.get("page_number"),
            excerpt=src["text"]
        ))

    db.commit()
    db.refresh(new_query)

    return QueryResponse(
        id=new_query.id,
        question=new_query.question,
        answer=new_query.answer,
        category=new_query.category,
        answer_status=new_query.answer_status,
        created_at=new_query.created_at,
        sources=source_responses
    )


@router.get("", response_model=List[QueryResponse])
def get_user_query_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100)
):
    """Retrieve recent queries. Students see their own; Admins see all."""
    query = db.query(QueryHistory)
    if current_user.role != "ADMIN":
        query = query.filter(QueryHistory.user_id == current_user.id)

    records = query.order_by(QueryHistory.created_at.desc()).limit(limit).all()

    result = []
    for rec in records:
        sources = [
            QuerySourceResponse(
                id=s.id,
                chunk_id=s.chunk_id,
                document_id=s.document_id,
                document_title=s.document_title,
                page_number=s.page_number,
                excerpt=s.excerpt
            )
            for s in rec.sources
        ]
        result.append(QueryResponse(
            id=rec.id,
            question=rec.question,
            answer=rec.answer,
            category=rec.category,
            answer_status=rec.answer_status,
            created_at=rec.created_at,
            sources=sources
        ))
    return result


@router.get("/{query_id}", response_model=QueryResponse)
def get_query_details(
    query_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full details of a specific query and its grounded sources."""
    rec = db.query(QueryHistory).filter(QueryHistory.id == query_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Query record not found")

    if current_user.role != "ADMIN" and rec.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this query")

    sources = [
        QuerySourceResponse(
            id=s.id,
            chunk_id=s.chunk_id,
            document_id=s.document_id,
            document_title=s.document_title,
            page_number=s.page_number,
            excerpt=s.excerpt
        )
        for s in rec.sources
    ]

    return QueryResponse(
        id=rec.id,
        question=rec.question,
        answer=rec.answer,
        category=rec.category,
        answer_status=rec.answer_status,
        created_at=rec.created_at,
        sources=sources
    )


@router.post("/{query_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_query_feedback(
    query_id: UUID,
    feedback_in: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit helpful / not helpful feedback for an AI response."""
    rec = db.query(QueryHistory).filter(QueryHistory.id == query_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Query record not found")

    fb = Feedback(
        query_id=query_id,
        user_id=current_user.id,
        rating=feedback_in.rating,
        comment=feedback_in.comment
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    return FeedbackResponse.model_validate(fb)
