"""Database setup and session management."""

import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/immo.db")

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create all tables."""
    os.makedirs("data", exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session."""
    with Session(engine) as session:
        yield session
