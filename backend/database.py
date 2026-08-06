"""Database configuration and session management for the Cortex API."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./cortex.db"
)

# SQLAlchemy's unqualified ``postgresql://`` URL selects the psycopg2 driver.
# This project ships psycopg 3 instead, so accept conventional PostgreSQL URLs
# while explicitly selecting the installed driver.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


async def get_db() -> AsyncGenerator[Session, None]:
    """Yield a database session for a single request."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
