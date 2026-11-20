from typing import List, Optional
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import AssignmentResponse, FeedbackResponse
from app.services.staff_service import StaffService
from app.dependencies.auth import require_staff
from app.models.user import User
from app.models.assignment import AssignmentStatus

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/assignments", response_model=List[AssignmentResponse])
def get_my_assignments(
    status: Optional[AssignmentStatus] = None,
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    service = StaffService(db)
    return service.get_staff_assignments(current_staff, status)


@router.get("/feedback", response_model=List[FeedbackResponse])
def get_my_feedback(
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    return StaffService(db).get_staff_feedback(current_staff)


@router.post("/assignments/{assignment_id}/respond", response_model=AssignmentResponse)
def respond_assignment(
    assignment_id: int,
    accept: bool = Body(..., embed=True),
    rejection_reason: Optional[str] = Body(None, embed=True),
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    service = StaffService(db)
    return service.respond_to_assignment(
        staff_user=current_staff,
        assignment_id=assignment_id,
        accept=accept,
        rejection_reason=rejection_reason,
    )


@router.post("/assignments/{assignment_id}/resolve", response_model=AssignmentResponse)
def resolve_assignment(
    assignment_id: int,
    resolution_notes: str = Body(..., embed=True),
    current_staff: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    service = StaffService(db)
    return service.resolve_assignment(
        staff_user=current_staff,
        assignment_id=assignment_id,
        resolution_notes=resolution_notes,
    )
