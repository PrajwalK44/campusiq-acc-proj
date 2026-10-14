// Types for CampusIQ API Models

export type UserRole = "STUDENT" | "FACULTY" | "ADMIN";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface QuerySource {
  id?: string;
  chunk_id: string;
  document_id?: string;
  document_title: string;
  page_number?: number;
  excerpt: string;
}

export interface QueryRecord {
  id: string;
  question: string;
  answer: string;
  category: string;
  answer_status: "ANSWERED" | "ABSTAINED" | "FAILED";
  created_at: string;
  sources: QuerySource[];
}

export interface Ticket {
  id: string;
  student_id: string;
  original_question: string;
  description?: string;
  category: string;
  assigned_faculty_id?: string;
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED";
  faculty_response?: string;
  created_at: string;
  updated_at: string;
  student_name?: string;
  faculty_name?: string;
}

export interface DocumentRecord {
  id: string;
  title: string;
  original_filename: string;
  category: string;
  upload_timestamp: string;
  processing_status: "PENDING" | "PROCESSING" | "INDEXED" | "FAILED";
  chunk_count: number;
  version: number;
  error_details?: string;
}

export interface AnalyticsOverview {
  total_queries: number;
  answered_queries: number;
  abstained_queries: number;
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  total_documents: number;
  indexed_documents: number;
}
