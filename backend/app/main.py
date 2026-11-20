from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.router import api_v1_router
from app.core.exceptions import CampusFixException
from app.db.session import DATABASE_URL, engine
from sqlalchemy import inspect, text

# Initialize structured logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="Industry-Grade Smart Campus Issue Reporting and Management Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json",
)


@app.on_event("startup")
def ensure_local_sqlite_schema():
    """Keep local SQLite installs usable when the API is started without Alembic."""
    if not DATABASE_URL.startswith("sqlite:"):
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "complaints" in tables:
        complaint_columns = {column["name"] for column in inspector.get_columns("complaints")}
        if "report_count" not in complaint_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE complaints ADD COLUMN report_count INTEGER NOT NULL DEFAULT 1"))
    if "complaint_feedbacks" in tables:
        feedback_columns = {column["name"] for column in inspector.get_columns("complaint_feedbacks")}
        if "staff_id" not in feedback_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE complaint_feedbacks ADD COLUMN staff_id INTEGER REFERENCES users(id)"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_complaint_feedbacks_staff_id ON complaint_feedbacks (staff_id)"))
                connection.execute(text("""
                    UPDATE complaint_feedbacks SET staff_id = (
                        SELECT staff_id FROM staff_assignments
                        WHERE staff_assignments.complaint_id = complaint_feedbacks.complaint_id
                          AND staff_assignments.status = 'COMPLETED'
                        ORDER BY completed_at DESC LIMIT 1
                    ) WHERE staff_id IS NULL
                """))

FAVICON_PATH = Path(__file__).resolve().parents[3] / "frontend" / "public" / "favicon.svg"

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CampusFixException)
async def campusfix_exception_handler(request: Request, exc: CampusFixException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message, "success": False},
    )


# Mount API Routers
app.include_router(api_v1_router, prefix=f"/api/{settings.API_VERSION}")


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    # Reuse the project's CampusFix SVG mark for browser favicon requests.
    return FileResponse(FAVICON_PATH, media_type="image/svg+xml")
