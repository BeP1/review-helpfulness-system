import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/reviews.db"
)


class Base(DeclarativeBase):
    pass


if DATABASE_URL.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import models

    Base.metadata.create_all(bind=engine)