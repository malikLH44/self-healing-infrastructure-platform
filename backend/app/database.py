
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    if engine is None:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    from app import models  # Register SQLAlchemy models

    Base.metadata.create_all(bind=engine)

    # Allow at most one open incident per service.
    # Resolved incidents remain in the history.
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                uq_incidents_one_open_per_service
                ON incidents (service)
                WHERE status = 'open'
                """
            )
        )
