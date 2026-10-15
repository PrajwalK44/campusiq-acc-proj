-- ==============================================================================
-- CampusIQ - Supabase PostgreSQL Relational Schema & Initial Seed
-- Run this script in the Supabase SQL Editor to set up all tables and indexes.
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('STUDENT', 'FACULTY', 'ADMIN')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'General',
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) NOT NULL DEFAULT 'PENDING' 
        CHECK (processing_status IN ('PENDING', 'PROCESSING', 'INDEXED', 'FAILED')),
    chunk_count INT NOT NULL DEFAULT 0,
    content_hash VARCHAR(64),
    version INT NOT NULL DEFAULT 1,
    error_details TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);

-- 3. Query History Table
CREATE TABLE IF NOT EXISTS query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'General',
    answer_status VARCHAR(50) NOT NULL DEFAULT 'ANSWERED' 
        CHECK (answer_status IN ('ANSWERED', 'ABSTAINED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_status ON query_history(answer_status);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);

-- 4. Query Sources Table
CREATE TABLE IF NOT EXISTS query_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES query_history(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    chunk_id VARCHAR(100) NOT NULL,
    document_title VARCHAR(255) NOT NULL,
    page_number INT,
    excerpt TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_query_sources_query_id ON query_sources(query_id);

-- 5. Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_question TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL DEFAULT 'General',
    assigned_faculty_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN' 
        CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')),
    faculty_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tickets_student_id ON tickets(student_id);
CREATE INDEX IF NOT EXISTS idx_tickets_faculty_id ON tickets(assigned_faculty_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);

-- 6. Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES query_history(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating VARCHAR(20) NOT NULL CHECK (rating IN ('HELPFUL', 'NOT_HELPFUL')),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_query_id ON feedback(query_id);

-- 7. Audit Events Table
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_events_actor_id ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);

-- ==============================================================================
-- Default Seed Users (Passwords are hashed for: "Password123!")
-- Hash: $2b$12$ZwFruLk1LqRiGAWi9sRYNOwM57YJNcDjiugIlNTxdq7g0D1TeGlCC
-- ==============================================================================
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES 
    ('System Administrator', 'admin@campusiq.edu', '$2b$12$ZwFruLk1LqRiGAWi9sRYNOwM57YJNcDjiugIlNTxdq7g0D1TeGlCC', 'ADMIN', true),
    ('Dr. Alan Turing', 'faculty@campusiq.edu', '$2b$12$ZwFruLk1LqRiGAWi9sRYNOwM57YJNcDjiugIlNTxdq7g0D1TeGlCC', 'FACULTY', true),
    ('Alex Johnson', 'student@campusiq.edu', '$2b$12$ZwFruLk1LqRiGAWi9sRYNOwM57YJNcDjiugIlNTxdq7g0D1TeGlCC', 'STUDENT', true)
ON CONFLICT (email) DO NOTHING;
