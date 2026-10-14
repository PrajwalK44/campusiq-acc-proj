import logging
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.db.session import get_db
from backend.app.rag.vector_store import VectorStoreService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health & Probes"])


@router.get("/health/live", status_code=status.HTTP_200_OK)
def liveness_probe():
    """Kubernetes Liveness Probe: confirms process is alive."""
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
def readiness_probe(response: Response, db: Session = Depends(get_db)):
    """
    Kubernetes Readiness Probe: checks connectivity to Supabase PostgreSQL
    and ChromaDB vector store.
    """
    checks = {
        "database": "unknown",
        "vector_store": "unknown"
    }

    # Test DB
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"Readiness DB check failed: {e}")
        checks["database"] = f"error: {str(e)}"

    # Test ChromaDB
    try:
        vs = VectorStoreService.get_instance()
        vs.collection.count()
        checks["vector_store"] = "ok"
    except Exception as e:
        logger.error(f"Readiness VectorStore check failed: {e}")
        checks["vector_store"] = f"error: {str(e)}"

    is_ready = checks["database"] == "ok" and checks["vector_store"] == "ok"
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks
    }
