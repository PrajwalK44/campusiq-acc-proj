import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta
import jwt

from backend.app.core.security import create_access_token, verify_password, get_password_hash
from backend.app.core.config import settings
from backend.app.rag.extractor import TextSplitter


def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_expiry():
    subject_id = "test-user-uuid"
    token = create_access_token(subject=subject_id, expires_delta=timedelta(minutes=10))
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == subject_id
    assert "exp" in decoded


def test_text_splitter_page_retention():
    sample_pages = [
        {"page_number": 1, "text": "This is page 1 content. Attendance must be at least 75% for exam eligibility."},
        {"page_number": 2, "text": "This is page 2 content. Grading policy is based on relative GPA scales."}
    ]
    chunks = TextSplitter.split_into_chunks(sample_pages, chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert "Attendance" in chunks[0]["text"] or "page 1" in chunks[0]["text"]


def test_rag_pipeline_abstention_on_empty_store():
    with patch("backend.app.rag.pipeline.VectorStoreService.get_instance") as mock_vs:
        mock_instance = MagicMock()
        mock_instance.query_similar.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        mock_vs.return_value = mock_instance

        with patch("backend.app.rag.pipeline.EmbeddingService.get_instance") as mock_es:
            mock_es_instance = MagicMock()
            mock_es_instance.encode.return_value = [[0.1, 0.2, 0.3]]
            mock_es.return_value = mock_es_instance

            from backend.app.rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            answer, status, sources = pipeline.answer_student_query("What is the hostel mess fee?")
            assert status == "ABSTAINED"
            assert "couldn't verify this information" in answer
            assert sources == []
