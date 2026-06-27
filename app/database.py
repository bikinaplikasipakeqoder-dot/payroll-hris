"""
Database configuration and session management for the Payroll & HRIS system.

Supports SQLite (Turso/libSQL compatible) with:
- Foreign key enforcement via PRAGMA
- WAL journal mode for concurrent read/write support
- FastAPI dependency injection via get_db()
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./payroll.db")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

# Build the SQLAlchemy-compatible engine URL. Turso URLs coming from the CLI
# start with libsql://, but the sqlalchemy-libsql dialect expects sqlite+libsql://
# with the auth token and secure=true in the query string.
if DATABASE_URL.startswith("libsql://"):
    import sqlalchemy_libsql  # noqa: F401  registers the sqlite.libsql dialect

    host_path = DATABASE_URL[len("libsql://"):]
    engine_url = f"sqlite+libsql://{host_path}?secure=true"
    engine = create_engine(
        engine_url,
        connect_args={"auth_token": TURSO_AUTH_TOKEN},
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_size=1,
        max_overflow=0,
        echo=False,
    )


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign key enforcement for local SQLite connections."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that provides a database session.

    Yields a SQLAlchemy session and ensures it is closed after use.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables defined in the models.

    Call this at application startup to ensure the schema is up to date.
    """
    Base.metadata.create_all(bind=engine)
