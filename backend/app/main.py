import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root is in sys.path so 'backend.app' can always be resolved
_ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.app.core.config import settings
from backend.app.api.auth import router as auth_router
from backend.app.api.users import router as users_router
from backend.app.api.queries import router as queries_router
from backend.app.api.documents import router as documents_router
from backend.app.api.tickets import router as tickets_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.health import router as health_router

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("campusiq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CampusIQ application...")
    logger.info(f"Environment: {settings.APP_ENV} | Model: {settings.LLM_MODEL}")
    yield
    logger.info("CampusIQ application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="CampusIQ: AI-Based Student Query Management System",
    lifespan=lifespan
)

# CORS Middleware for Next.js frontend communication
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics Instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Register Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(queries_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(tickets_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health": "/health/ready",
        "metrics": "/metrics"
    }
