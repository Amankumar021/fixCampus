from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4
import logging
from app.db.session import get_db
from app.schemas.schemas import (
    ComplaintCreate,
    ComplaintResponse,
    FeedbackCreate,
    FeedbackResponse,
    TimelineResponse,
)
from app.services.complaint_service import ComplaintService
from app.repositories.assignment_repo import ActivityRepository
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from app.core.config import settings

router = APIRouter(prefix="/complaints", tags=["Complaints"])
logger = logging.getLogger("campusfix.uploads")
ALLOWED_UPLOAD_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}


@router.get("/attachments/{filename}")
def download_complaint_attachment(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # UUID-only names prevent path traversal; access is checked against the complaint.
    if Path(filename).name != filename or Path(filename).suffix.lower() not in ALLOWED_UPLOAD_TYPES.values():
        raise HTTPException(status_code=404, detail="Attachment not found.")
    attachment_url = f"/uploads/{filename}"
    complaint = db.query(Complaint).filter(Complaint.attachment_url == attachment_url).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    if current_user.role == UserRole.STUDENT and complaint.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    ComplaintService(db).get_complaint(complaint.id, current_user)
    path = Path(settings.UPLOAD_DIR).expanduser().resolve() / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment not found.")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)


@router.post("/attachments", status_code=status.HTTP_201_CREATED)
async def upload_complaint_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can upload complaint evidence.")
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, WebP, and PDF attachments are allowed.")
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read(max_size + 1)
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    signatures = {
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        "application/pdf": content.startswith(b"%PDF-"),
    }
    if not signatures[file.content_type]:
        raise HTTPException(status_code=415, detail="File content does not match its declared type.")
    filename = f"{uuid4().hex}{ALLOWED_UPLOAD_TYPES[file.content_type]}"
    upload_dir = Path(settings.UPLOAD_DIR).expanduser().resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(content)
    logger.info("Complaint attachment stored for user_id=%s file=%s", current_user.id, filename)
    return {"attachment_url": f"/uploads/{filename}", "filename": filename}


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def lodge_complaint(
    complaint_in: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.create_complaint(current_user, complaint_in)


@router.get("", response_model=List[ComplaintResponse])
def list_complaints(
    status: Optional[ComplaintStatus] = None,
    category: Optional[str] = None,
    priority: Optional[ComplaintPriority] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.list_complaints(
        current_user=current_user,
        status=status,
        category=category,
        priority=priority,
        skip=skip,
        limit=limit,
    )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_by_id(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.get_complaint(complaint_id, current_user)


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: int,
    target_status: ComplaintStatus,
    comment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.transition_status(complaint_id, target_status, current_user, comment)


@router.get("/{complaint_id}/timeline", response_model=List[TimelineResponse])
def get_complaint_timeline(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify access to complaint first
    ComplaintService(db).get_complaint(complaint_id, current_user)
    return ActivityRepository(db).get_timeline_by_complaint(complaint_id)


@router.post("/{complaint_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_complaint_feedback(
    complaint_id: int,
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.submit_feedback(complaint_id, current_user, feedback_in)


@router.get("/{complaint_id}/feedback", response_model=Optional[FeedbackResponse])
def get_complaint_feedback(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ComplaintService(db).get_complaint(complaint_id, current_user)
    return ActivityRepository(db).get_feedback(complaint_id)
