from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("sqlite:"):
    database_path = DATABASE_URL.removeprefix("sqlite:///")
    if database_path != ":memory:":
        Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
