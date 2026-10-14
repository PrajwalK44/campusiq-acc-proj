from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import get_db
from backend.app.core.security import get_current_user, require_role
from backend.app.models.entities import User, QueryHistory, Ticket, Document
from backend.app.schemas.api_models import (
    AnalyticsOverview,
    TopicStatistic,
    UnansweredQuerySummary
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Oversight"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Admin-only: Aggregate system metrics from actual Supabase records."""
    total_queries = db.query(func.count(QueryHistory.id)).scalar() or 0
    answered_queries = db.query(func.count(QueryHistory.id)).filter(QueryHistory.answer_status == "ANSWERED").scalar() or 0
    abstained_queries = db.query(func.count(QueryHistory.id)).filter(QueryHistory.answer_status == "ABSTAINED").scalar() or 0

    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
    open_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "OPEN").scalar() or 0
    resolved_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "RESOLVED").scalar() or 0

    total_documents = db.query(func.count(Document.id)).scalar() or 0
    indexed_documents = db.query(func.count(Document.id)).filter(Document.processing_status == "INDEXED").scalar() or 0

    return AnalyticsOverview(
        total_queries=total_queries,
        answered_queries=answered_queries,
        abstained_queries=abstained_queries,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        total_documents=total_documents,
        indexed_documents=indexed_documents
    )


@router.get("/topics", response_model=List[TopicStatistic])
def get_topic_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Admin-only: Breakdown of query frequency by category."""
    rows = (
        db.query(QueryHistory.category, func.count(QueryHistory.id))
        .group_by(QueryHistory.category)
        .order_by(func.count(QueryHistory.id).desc())
        .all()
    )
    return [TopicStatistic(category=row[0] or "General", query_count=row[1]) for row in rows]


@router.get("/unanswered", response_model=List[UnansweredQuerySummary])
def get_unanswered_queries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Admin-only: Unanswered/abstained questions highlighting knowledge gaps."""
    records = (
        db.query(QueryHistory)
        .filter(QueryHistory.answer_status == "ABSTAINED")
        .order_by(QueryHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        UnansweredQuerySummary(
            id=r.id,
            question=r.question,
            category=r.category,
            created_at=r.created_at
        )
        for r in records
    ]
