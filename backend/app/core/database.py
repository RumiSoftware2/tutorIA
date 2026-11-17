from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache(maxsize=4)
def _engine_for_url(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2)


def create_database_engine(database_url: str | None = None) -> Engine:
    """Return a pooled synchronous engine for an explicit or configured URL."""
    url = database_url or get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL no está configurada. Añádela al archivo .env antes de usar la base de datos.")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return _engine_for_url(url)


def get_db() -> Generator[Session, None, None]:
    db = create_session()
    try:
        yield db
    finally:
        db.close()


def create_session() -> Session:
    """Create a short-lived synchronous session using the shared engine pool."""
    engine = create_database_engine()
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory()
