from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.security import get_current_user, require_role
from backend.app.models.entities import User, Ticket
from backend.app.schemas.api_models import (
    TicketCreate,
    TicketUpdate,
    TicketResponseSubmit,
    TicketResponse
)

router = APIRouter(prefix="/tickets", tags=["Tickets & Escalation"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Student creates a ticket escalating an unanswered or unclear query."""
    new_ticket = Ticket(
        student_id=current_user.id,
        original_question=ticket_in.original_question,
        description=ticket_in.description,
        category=ticket_in.category or "General",
        status="OPEN"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return TicketResponse(
        id=new_ticket.id,
        student_id=new_ticket.student_id,
        original_question=new_ticket.original_question,
        description=new_ticket.description,
        category=new_ticket.category,
        assigned_faculty_id=new_ticket.assigned_faculty_id,
        status=new_ticket.status,
        faculty_response=new_ticket.faculty_response,
        created_at=new_ticket.created_at,
        updated_at=new_ticket.updated_at,
        student_name=current_user.full_name
    )


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List tickets according to role:
    - STUDENT: only tickets created by this student.
    - FACULTY: tickets assigned to this faculty member or unassigned open tickets.
    - ADMIN: all tickets.
    """
    query = db.query(Ticket)

    if current_user.role == "STUDENT":
        query = query.filter(Ticket.student_id == current_user.id)
    elif current_user.role == "FACULTY":
        query = query.filter(
            (Ticket.assigned_faculty_id == current_user.id) |
            (Ticket.assigned_faculty_id.is_(None))
        )

    if status_filter:
        query = query.filter(Ticket.status == status_filter)

    tickets = query.order_by(Ticket.created_at.desc()).all()

    result = []
    for t in tickets:
        student_name = t.student.full_name if t.student else None
        faculty_name = t.faculty.full_name if t.faculty else None
        result.append(TicketResponse(
            id=t.id,
            student_id=t.student_id,
            original_question=t.original_question,
            description=t.description,
            category=t.category,
            assigned_faculty_id=t.assigned_faculty_id,
            status=t.status,
            faculty_response=t.faculty_response,
            created_at=t.created_at,
            updated_at=t.updated_at,
            student_name=student_name,
            faculty_name=faculty_name
        ))
    return result


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket_details(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch single ticket details."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.role == "STUDENT" and ticket.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")

    student_name = ticket.student.full_name if ticket.student else None
    faculty_name = ticket.faculty.full_name if ticket.faculty else None

    return TicketResponse(
        id=ticket.id,
        student_id=ticket.student_id,
        original_question=ticket.original_question,
        description=ticket.description,
        category=ticket.category,
        assigned_faculty_id=ticket.assigned_faculty_id,
        status=ticket.status,
        faculty_response=ticket.faculty_response,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        student_name=student_name,
        faculty_name=faculty_name
    )


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """Faculty/Admin: Reassign ticket or update workflow status."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket_update.status:
        ticket.status = ticket_update.status
    if ticket_update.assigned_faculty_id:
        ticket.assigned_faculty_id = ticket_update.assigned_faculty_id

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)

    student_name = ticket.student.full_name if ticket.student else None
    faculty_name = ticket.faculty.full_name if ticket.faculty else None

    return TicketResponse(
        id=ticket.id,
        student_id=ticket.student_id,
        original_question=ticket.original_question,
        description=ticket.description,
        category=ticket.category,
        assigned_faculty_id=ticket.assigned_faculty_id,
        status=ticket.status,
        faculty_response=ticket.faculty_response,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        student_name=student_name,
        faculty_name=faculty_name
    )


@router.post("/{ticket_id}/responses", response_model=TicketResponse)
def submit_faculty_response(
    ticket_id: UUID,
    response_in: TicketResponseSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """Faculty/Admin: Provide official response to a student's escalated ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.faculty_response = response_in.faculty_response
    ticket.status = response_in.status or "RESOLVED"
    if not ticket.assigned_faculty_id:
        ticket.assigned_faculty_id = current_user.id
    ticket.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)

    student_name = ticket.student.full_name if ticket.student else None
    faculty_name = ticket.faculty.full_name if ticket.faculty else None

    return TicketResponse(
        id=ticket.id,
        student_id=ticket.student_id,
        original_question=ticket.original_question,
        description=ticket.description,
        category=ticket.category,
        assigned_faculty_id=ticket.assigned_faculty_id,
        status=ticket.status,
        faculty_response=ticket.faculty_response,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        student_name=student_name,
        faculty_name=faculty_name
    )
