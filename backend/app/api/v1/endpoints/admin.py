from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import (
    StaffCreate,
    UserResponse,
    AssignmentCreate,
    AssignmentResponse,
    ComplaintResponse,
    ComplaintUpdate,
    FeedbackResponse,
)
from app.services.staff_service import StaffService
from app.services.complaint_service import ComplaintService
from app.dependencies.auth import require_admin
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])


class StaffActiveUpdate(BaseModel):
    is_active: bool


class StaffFeedbackItem(BaseModel):
    staff: UserResponse
    average_rating: Optional[float]
    rating_count: int
    feedback: List[FeedbackResponse]


@router.post("/staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff_user(
    staff_in: StaffCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = StaffService(db)
    return service.create_staff_account(admin_user, staff_in)


@router.get("/staff", response_model=List[UserResponse])
def list_all_staff(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = StaffService(db)
    return service.list_staff()


@router.get("/staff/performance", response_model=List[StaffFeedbackItem])
def get_staff_performance(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return StaffService(db).get_staff_performance(admin_user)


@router.patch("/staff/{staff_id}/active", response_model=UserResponse)
def set_staff_active(
    staff_id: int,
    update_in: StaffActiveUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return StaffService(db).set_staff_active(admin_user, staff_id, update_in.is_active)


@router.post("/assign", response_model=AssignmentResponse)
def assign_complaint(
    assign_in: AssignmentCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = StaffService(db)
    return service.assign_complaint_to_staff(
        admin_user=admin_user,
        complaint_id=assign_in.complaint_id,
        staff_id=assign_in.staff_id,
    )


@router.patch("/complaints/{complaint_id}", response_model=ComplaintResponse)
def update_complaint_admin(
    complaint_id: int,
    update_in: ComplaintUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = ComplaintService(db)
    return service.update_complaint_admin(
        complaint_id=complaint_id,
        admin_user=admin_user,
        category=update_in.category,
        priority=update_in.priority,
        status=update_in.status,
    )
