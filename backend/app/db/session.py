import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

from urllib.parse import quote_plus, unquote


def format_database_url(url: str) -> str:
    """Ensure standard postgresql:// scheme and properly escape URI credentials."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Sanitize special characters (such as '@') in the password if unencoded
    prefix, sep, rest = url.partition("://")
    if sep and rest.count("@") > 1:
        userinfo, _, hostinfo = rest.rpartition("@")
        user, colon, pwd = userinfo.partition(":")
        if colon:
            clean_pwd = quote_plus(unquote(pwd))
            url = f"{prefix}://{user}:{clean_pwd}@{hostinfo}"

    return url


db_url = format_database_url(settings.DATABASE_URL)

# SSL is required when connecting to Supabase or remote cloud PostgreSQL instances
connect_args = {}
if "sslmode" not in db_url:
    lower_url = db_url.lower()
    if "supabase" in lower_url or "pooler" in lower_url:
        connect_args["sslmode"] = "require"

# Configure engine with pooling suitable for Supabase (Session Pooler or Direct)
# Note: pool_pre_ping ensures stale pooler connections are re-validated
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session for FastAPI request contexts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
