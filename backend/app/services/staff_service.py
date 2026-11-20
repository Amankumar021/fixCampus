from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.models.assignment import StaffAssignment, AssignmentStatus
from app.models.activity import ComplaintTimeline
from app.models.auth_session import RefreshSession
from app.schemas.schemas import StaffCreate
from app.core.security import get_password_hash
from app.core.exceptions import (
    EntityNotFoundException,
    ForbiddenOperationException,
    DuplicateResourceException,
)
from app.repositories.user_repo import UserRepository
from app.repositories.complaint_repo import ComplaintRepository
from app.repositories.assignment_repo import AssignmentRepository, ActivityRepository


class StaffService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.complaint_repo = ComplaintRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.activity_repo = ActivityRepository(db)

    def create_staff_account(self, admin_user: User, staff_in: StaffCreate) -> User:
        if admin_user.role != UserRole.ADMIN:
            raise ForbiddenOperationException("Only administrators can create staff accounts.")

        existing = self.user_repo.get_by_email(staff_in.email)
        if existing:
            raise DuplicateResourceException("User", "email", staff_in.email)

        staff_user = User(
            email=staff_in.email.lower().strip(),
            hashed_password=get_password_hash(staff_in.password),
            full_name=staff_in.full_name.strip(),
            role=UserRole.STAFF,
            department=staff_in.department.strip(),
            phone_number=staff_in.phone_number,
        )
        return self.user_repo.create(staff_user)

    def list_staff(self) -> List[User]:
        return self.user_repo.get_users_by_role(UserRole.STAFF, include_inactive=True)

    def set_staff_active(self, admin_user: User, staff_id: int, active: bool) -> User:
        if admin_user.role != UserRole.ADMIN:
            raise ForbiddenOperationException("Only administrators can manage staff accounts.")
        staff = self.user_repo.get_by_id(staff_id)
        if not staff or staff.role != UserRole.STAFF:
            raise EntityNotFoundException("Staff User", staff_id)
        if staff.is_active == active:
            return staff
        staff.is_active = active
        if not active:
            staff.token_version += 1
            self.db.query(RefreshSession).filter(
                RefreshSession.user_id == staff.id,
                RefreshSession.revoked_at.is_(None),
            ).update({RefreshSession.revoked_at: datetime.now(timezone.utc)}, synchronize_session=False)
        self.db.commit()
        self.db.refresh(staff)
        return staff

    def assign_complaint_to_staff(
        self,
        admin_user: User,
        complaint_id: int,
        staff_id: int,
    ) -> StaffAssignment:
        if admin_user.role != UserRole.ADMIN:
            raise ForbiddenOperationException("Only administrators can assign complaints to staff.")

        complaint = self.complaint_repo.get_by_id(complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", complaint_id)

        staff = self.user_repo.get_by_id(staff_id)
        if not staff or staff.role != UserRole.STAFF:
            raise EntityNotFoundException("Staff User", staff_id)
        if not staff.is_active:
            raise ForbiddenOperationException("Inactive staff accounts cannot receive assignments.")

        if complaint.status not in [ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.REOPENED, ComplaintStatus.ASSIGNED]:
            raise ForbiddenOperationException("Only open complaints can be assigned or reassigned.")

        # Persist assignment, status, and timeline in one transaction.
        assignment = StaffAssignment(
            complaint_id=complaint_id,
            staff_id=staff_id,
            assigned_by_id=admin_user.id,
            status=AssignmentStatus.PENDING,
        )
        self.db.add(assignment)
        previous_status = complaint.status
        complaint.status = ComplaintStatus.ASSIGNED
        self.db.add(ComplaintTimeline(
            complaint_id=complaint.id, actor_id=admin_user.id,
            action="ASSIGNED_TO_STAFF", previous_status=previous_status.value,
            new_status=ComplaintStatus.ASSIGNED.value,
            comment=f"Assigned to {staff.full_name} ({staff.department})",
        ))
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_staff_assignments(self, staff_user: User, status: Optional[AssignmentStatus] = None) -> List[StaffAssignment]:
        if staff_user.role != UserRole.STAFF:
            raise ForbiddenOperationException("Only maintenance staff can view assigned tasks.")
        return self.assignment_repo.get_by_staff(staff_user.id, status)

    def get_staff_feedback(self, staff_user: User):
        if staff_user.role != UserRole.STAFF:
            raise ForbiddenOperationException("Only maintenance staff can view staff feedback.")
        from app.repositories.assignment_repo import ActivityRepository
        return ActivityRepository(self.db).get_feedback_for_staff(staff_user.id)

    def get_staff_performance(self, admin_user: User):
        if admin_user.role != UserRole.ADMIN:
            raise ForbiddenOperationException("Only administrators can view staff performance.")
        from sqlalchemy import func
        from app.models.activity import ComplaintFeedback
        staff = self.user_repo.get_users_by_role(UserRole.STAFF, include_inactive=True)
        result = []
        for member in staff:
            ratings = self.db.query(
                func.avg(ComplaintFeedback.rating), func.count(ComplaintFeedback.id)
            ).filter(ComplaintFeedback.staff_id == member.id).one()
            feedback = ActivityRepository(self.db).get_feedback_for_staff(member.id)
            result.append({
                "staff": member,
                "average_rating": round(float(ratings[0]), 1) if ratings[0] is not None else None,
                "rating_count": ratings[1],
                "feedback": feedback,
            })
        return result

    def respond_to_assignment(
        self,
        staff_user: User,
        assignment_id: int,
        accept: bool,
        rejection_reason: Optional[str] = None,
    ) -> StaffAssignment:
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise EntityNotFoundException("Assignment", assignment_id)

        if assignment.staff_id != staff_user.id:
            raise ForbiddenOperationException("You cannot respond to another staff member's assignment.")

        complaint = self.complaint_repo.get_by_id(assignment.complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", assignment.complaint_id)

        if assignment.status != AssignmentStatus.PENDING:
            raise ForbiddenOperationException("Only pending assignments can be accepted or rejected.")

        if accept:
            assignment.status = AssignmentStatus.ACCEPTED
            assignment.responded_at = datetime.now(timezone.utc)
            complaint.status = ComplaintStatus.IN_PROGRESS
            comment = f"Assignment accepted by staff {staff_user.full_name}. Work is in progress."
        else:
            assignment.status = AssignmentStatus.REJECTED
            assignment.rejection_reason = rejection_reason or "Staff unavailable"
            assignment.responded_at = datetime.now(timezone.utc)
            complaint.status = ComplaintStatus.UNDER_REVIEW
            comment = f"Assignment rejected by staff {staff_user.full_name}. Reason: {assignment.rejection_reason}"

        self.db.add_all([assignment, complaint, ComplaintTimeline(
            complaint_id=complaint.id, actor_id=staff_user.id,
            action="ASSIGNMENT_RESPONSE", previous_status=ComplaintStatus.ASSIGNED.value,
            new_status=complaint.status.value, comment=comment,
        )])
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def resolve_assignment(
        self,
        staff_user: User,
        assignment_id: int,
        resolution_notes: str,
    ) -> StaffAssignment:
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise EntityNotFoundException("Assignment", assignment_id)

        if assignment.staff_id != staff_user.id:
            raise ForbiddenOperationException("You cannot resolve another staff member's assignment.")
        if assignment.status != AssignmentStatus.ACCEPTED:
            raise ForbiddenOperationException("Only accepted assignments can be resolved.")

        assignment.status = AssignmentStatus.COMPLETED
        assignment.resolution_notes = resolution_notes.strip()
        assignment.completed_at = datetime.now(timezone.utc)

        complaint = self.complaint_repo.get_by_id(assignment.complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", assignment.complaint_id)
        if complaint.status != ComplaintStatus.IN_PROGRESS:
            raise ForbiddenOperationException("Only in-progress complaints can be resolved.")
        complaint.status = ComplaintStatus.RESOLVED
        complaint.resolved_at = datetime.now(timezone.utc)

        self.db.add_all([assignment, complaint, ComplaintTimeline(
            complaint_id=complaint.id, actor_id=staff_user.id,
            action="COMPLAINT_RESOLVED", previous_status=ComplaintStatus.IN_PROGRESS.value,
            new_status=ComplaintStatus.RESOLVED.value,
            comment=f"Work completed. Notes: {resolution_notes}",
        )])
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
