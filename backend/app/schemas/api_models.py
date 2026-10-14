from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==========================================
# Auth & User Schemas
# ==========================================
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "STUDENT"  # STUDENT, FACULTY, ADMIN


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==========================================
# Document Schemas
# ==========================================
class DocumentResponse(BaseModel):
    id: UUID
    title: str
    original_filename: str
    category: str
    uploaded_by: Optional[UUID] = None
    upload_timestamp: datetime
    processing_status: str
    chunk_count: int
    version: int
    error_details: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# RAG & Query Schemas
# ==========================================
class QuerySourceResponse(BaseModel):
    id: Optional[UUID] = None
    chunk_id: str
    document_id: Optional[UUID] = None
    document_title: str
    page_number: Optional[int] = None
    excerpt: str

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    category: Optional[str] = "General"


class QueryResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    category: str
    answer_status: str  # ANSWERED, ABSTAINED, FAILED
    created_at: datetime
    sources: List[QuerySourceResponse] = []

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    rating: str = Field(..., pattern="^(HELPFUL|NOT_HELPFUL)$")
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: UUID
    query_id: UUID
    user_id: UUID
    rating: str
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Ticket Schemas
# ==========================================
class TicketCreate(BaseModel):
    original_question: str
    description: Optional[str] = None
    category: Optional[str] = "General"


class TicketUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(OPEN|IN_PROGRESS|RESOLVED)$")
    assigned_faculty_id: Optional[UUID] = None


class TicketResponseSubmit(BaseModel):
    faculty_response: str = Field(..., min_length=1)
    status: Optional[str] = "RESOLVED"


class TicketResponse(BaseModel):
    id: UUID
    student_id: UUID
    original_question: str
    description: Optional[str] = None
    category: str
    assigned_faculty_id: Optional[UUID] = None
    status: str
    faculty_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    faculty_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# Analytics Schemas
# ==========================================
class AnalyticsOverview(BaseModel):
    total_queries: int
    answered_queries: int
    abstained_queries: int
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    total_documents: int
    indexed_documents: int


class TopicStatistic(BaseModel):
    category: str
    query_count: int


class UnansweredQuerySummary(BaseModel):
    id: UUID
    question: str
    category: str
    created_at: datetime
