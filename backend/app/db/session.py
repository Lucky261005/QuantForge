"""SQLAlchemy engine/session setup — dialect-agnostic across SQLite and Postgres."""

from collections.abc import Generator

import numpy as np
from psycopg2.extensions import adapt, register_adapter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
# SQLite has no real concurrent-connection story (single-writer file lock), so pool
# sizing only matters — and is only safe to pass to create_engine — for Postgres.
pool_kwargs = (
    {}
    if settings.is_sqlite
    else {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT_SECONDS,
    }
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    **pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# psycopg2 renders floats with repr(), which NumPy 2 turns into "np.float64(1.0)", invalid SQL.
# Engine and metric outputs are numpy scalars, so adapt them as plain Python numbers.
register_adapter(np.floating, lambda v: adapt(float(v)))
register_adapter(np.integer, lambda v: adapt(int(v)))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
