"""Connection to the garden-main-api's SQLite database."""

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

engine = create_engine(
    f"sqlite:///{DATA_DIR / 'garden.db'}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for the SQLAlchemy models."""


def init_db() -> None:
    """Creates the data folder and any tables that don't exist yet."""
    from app import models  # noqa: F401 - registers the models before create_all

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Opens a database session per request.

    Yields:
        SQLAlchemy session, closed at the end of the request.
    """
    with SessionLocal() as session:
        yield session
