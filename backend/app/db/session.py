from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def _database_url():
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///./"):
        relative_path = url.removeprefix("sqlite:///./")
        root = Path(__file__).resolve().parents[3]
        return f"sqlite:///{(root / relative_path).resolve().as_posix()}"
    return url


DATABASE_URL = _database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and False,
)

if DATABASE_URL.startswith("sqlite:"):
    database_path = DATABASE_URL.removeprefix("sqlite:///")
    if database_path != ":memory:":
        Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
