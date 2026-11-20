from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from app.models.activity import ComplaintTimeline, ComplaintFeedback
from app.models.reward import RewardTransaction
from app.models.assignment import StaffAssignment, AssignmentStatus
from app.schemas.schemas import ComplaintCreate, FeedbackCreate
from app.repositories.complaint_repo import ComplaintRepository
from app.repositories.assignment_repo import ActivityRepository
from app.ml.inference import predict_complaint_category
from app.core.exceptions import (
    EntityNotFoundException,
    ForbiddenOperationException,
    InvalidStateTransitionException,
)

# Allowed State Transitions
ALLOWED_TRANSITIONS: Dict[ComplaintStatus, List[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: [ComplaintStatus.UNDER_REVIEW, ComplaintStatus.ASSIGNED, ComplaintStatus.REJECTED],
    ComplaintStatus.UNDER_REVIEW: [ComplaintStatus.ASSIGNED, ComplaintStatus.REJECTED],
    ComplaintStatus.ASSIGNED: [ComplaintStatus.IN_PROGRESS, ComplaintStatus.REJECTED],
    ComplaintStatus.IN_PROGRESS: [ComplaintStatus.RESOLVED, ComplaintStatus.ASSIGNED],
    ComplaintStatus.RESOLVED: [ComplaintStatus.CLOSED, ComplaintStatus.REOPENED],
    ComplaintStatus.REOPENED: [ComplaintStatus.UNDER_REVIEW, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS],
    ComplaintStatus.CLOSED: [ComplaintStatus.REOPENED],
    ComplaintStatus.REJECTED: [ComplaintStatus.UNDER_REVIEW],
}


class ComplaintService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ComplaintRepository(db)
        self.activity_repo = ActivityRepository(db)

    def create_complaint(self, student: User, complaint_in: ComplaintCreate) -> Complaint:
        if student.role != UserRole.STUDENT:
            raise ForbiddenOperationException("Only students can submit campus complaints.")
        if complaint_in.attachment_url:
            filename = complaint_in.attachment_url.removeprefix("/uploads/")
            if complaint_in.attachment_url != f"/uploads/{filename}" or not filename or "/" in filename or "\\" in filename:
                raise ForbiddenOperationException("Attachment reference is invalid.")
            if self.db.query(Complaint.id).filter(Complaint.attachment_url == complaint_in.attachment_url).first():
                raise ForbiddenOperationException("This attachment is already linked to another complaint.")
            from pathlib import Path
            from app.core.config import settings
            if not (Path(settings.UPLOAD_DIR).expanduser().resolve() / filename).is_file():
                raise EntityNotFoundException("Complaint attachment", filename)
        # Run ML inference on complaint description
        ml_result = predict_complaint_category(f"{complaint_in.title} {complaint_in.description}")
        predicted_cat = ml_result["predicted_category"]
        confidence = ml_result["confidence"]

        # If user explicitly selected category, respect it; otherwise use predicted category
        final_category = complaint_in.category if complaint_in.category else (predicted_cat if ml_result["is_confident"] else "Other")
        is_overridden = bool(complaint_in.category and complaint_in.category != predicted_cat)

        # Normalize whitespace and case so small formatting differences do not
        # create separate campus issues. A match requires same location/category
        # and a materially similar title or description.
        normalized_location = " ".join(complaint_in.location.casefold().split())
        normalized_category = " ".join(final_category.casefold().split())
        existing = self.db.query(Complaint).filter(
            func.lower(func.trim(Complaint.location)) == normalized_location,
            func.lower(func.trim(Complaint.category)) == normalized_category,
            Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.REJECTED]),
        ).order_by(Complaint.created_at.desc()).all()
        def issue_tokens(title: str, description: str) -> set[str]:
            ignored = {"the", "and", "for", "near", "with", "from", "this", "that", "have", "has", "was", "are", "our", "not", "into", "when", "where"}
            return {word.strip(".,!?;:()[]{}\"'") for word in f"{title} {description}".casefold().split()
                    if len(word.strip(".,!?;:()[]{}\"'")) > 2 and word.strip(".,!?;:()[]{}\"'") not in ignored}

        incoming_words = issue_tokens(complaint_in.title, complaint_in.description)
        duplicate = next((item for item in existing if (
            len(incoming_words & issue_tokens(item.title, item.description)) >= 2
        )), None)
        if duplicate:
            duplicate.report_count = (duplicate.report_count or 1) + 1
            priority_order = [ComplaintPriority.LOW, ComplaintPriority.MEDIUM, ComplaintPriority.HIGH, ComplaintPriority.CRITICAL]
            current_index = priority_order.index(duplicate.priority)
            if current_index < len(priority_order) - 1:
                duplicate.priority = priority_order[current_index + 1]
            self.db.add(ComplaintTimeline(
                complaint_id=duplicate.id,
                actor_id=student.id,
                action="DUPLICATE_REPORT_ADDED",
                previous_status=duplicate.status.value,
                new_status=duplicate.status.value,
                comment=f"A matching report was added. Total reports: {duplicate.report_count}; priority raised to {duplicate.priority.value}.",
            ))
            self.db.commit()
            self.db.refresh(duplicate)
            duplicate.reward_points_awarded = 0
            return duplicate

        new_complaint = Complaint(
            title=complaint_in.title.strip(),
            description=complaint_in.description.strip(),
            location=complaint_in.location.strip(),
            category=final_category,
            predicted_category=predicted_cat,
            prediction_confidence=confidence,
            is_category_overridden=is_overridden,
            priority=complaint_in.priority or ComplaintPriority.MEDIUM,
            status=ComplaintStatus.SUBMITTED,
            attachment_url=complaint_in.attachment_url,
            student_id=student.id,
        )
        self.db.add(new_complaint)
        self.db.flush()
        self.db.add(ComplaintTimeline(
            complaint_id=new_complaint.id,
            actor_id=student.id,
            action="COMPLAINT_SUBMITTED",
            previous_status=None,
            new_status=ComplaintStatus.SUBMITTED.value,
            comment=f"Complaint lodged with AI predicted category: {predicted_cat} (confidence signal: {confidence})",
        ))
        issue_reward_awarded = self._award_points(student, new_complaint, 10, "ISSUE_REPORTED")
        self.db.commit()
        self.db.refresh(new_complaint)
        new_complaint.reward_points_awarded = 10 if issue_reward_awarded else 0
        return new_complaint

    def get_complaint(self, complaint_id: int, current_user: User) -> Complaint:
        complaint = self.repo.get_by_id(complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", complaint_id)

        # RBAC Check: Student can only view their own complaint
        if current_user.role == UserRole.STUDENT and complaint.student_id != current_user.id:
            raise ForbiddenOperationException("Access denied: You can only view your own complaints.")
        if current_user.role == UserRole.STAFF:
            assigned = self.db.query(StaffAssignment.id).filter(
                StaffAssignment.complaint_id == complaint_id,
                StaffAssignment.staff_id == current_user.id,
            ).first()
            if not assigned:
                raise ForbiddenOperationException("You can only view complaints assigned to you.")

        return complaint

    def list_complaints(
        self,
        current_user: User,
        status: Optional[ComplaintStatus] = None,
        category: Optional[str] = None,
        priority: Optional[ComplaintPriority] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Complaint]:
        # If student, limit only to their complaints
        student_id = current_user.id if current_user.role == UserRole.STUDENT else None
        staff_id = current_user.id if current_user.role == UserRole.STAFF else None
        return self.repo.get_all(
            status=status,
            category=category,
            priority=priority,
            student_id=student_id,
            staff_id=staff_id,
            skip=skip,
            limit=limit,
        )

    def transition_status(
        self,
        complaint_id: int,
        target_status: ComplaintStatus,
        actor: User,
        comment: Optional[str] = None,
    ) -> Complaint:
        complaint = self.repo.get_by_id(complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", complaint_id)

        current_status = complaint.status

        # Permission rules for status transitions:
        if actor.role == UserRole.STUDENT:
            # Student can only REOPEN if resolved or closed, or CLOSE if resolved
            if target_status not in [ComplaintStatus.REOPENED, ComplaintStatus.CLOSED]:
                raise ForbiddenOperationException("Students can only close or reopen resolved complaints.")
            if complaint.student_id != actor.id:
                raise ForbiddenOperationException("You cannot transition another student's complaint.")
        elif actor.role == UserRole.STAFF:
            # Staff can transition between ASSIGNED, IN_PROGRESS, RESOLVED
            if target_status not in [ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED]:
                raise ForbiddenOperationException("Staff can only move assigned complaints to in-progress or resolved.")
            assignment = self.db.query(StaffAssignment).filter(
                StaffAssignment.complaint_id == complaint_id,
                StaffAssignment.staff_id == actor.id,
                StaffAssignment.status == AssignmentStatus.ACCEPTED,
            ).first()
            if not assignment:
                raise ForbiddenOperationException("You can only update complaints assigned to you.")
        elif actor.role != UserRole.ADMIN:
            raise ForbiddenOperationException("Operation not permitted.")

        # Check state machine graph
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise InvalidStateTransitionException(current_status.value, target_status.value)

        # Apply transition
        complaint.status = target_status
        if target_status == ComplaintStatus.RESOLVED:
            complaint.resolved_at = datetime.now(timezone.utc)

        self.db.add(ComplaintTimeline(
            complaint_id=complaint.id,
            actor_id=actor.id,
            action="STATUS_CHANGED",
            previous_status=current_status.value,
            new_status=target_status.value,
            comment=comment or f"Status transitioned from {current_status.value} to {target_status.value}",
        ))
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def update_complaint_admin(
        self,
        complaint_id: int,
        admin_user: User,
        category: Optional[str] = None,
        priority: Optional[ComplaintPriority] = None,
        status: Optional[ComplaintStatus] = None,
    ) -> Complaint:
        if admin_user.role != UserRole.ADMIN:
            raise ForbiddenOperationException("Only administrators can perform administrative complaint updates.")

        complaint = self.repo.get_by_id(complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", complaint_id)

        comment_parts = []
        current_status = complaint.status
        if category and category != complaint.category:
            comment_parts.append(f"Category changed from {complaint.category} to {category}")
            complaint.category = category
            complaint.is_category_overridden = True
        if category:
            complaint.category_reviewed_at = datetime.now(timezone.utc)
            complaint.category_reviewed_by_id = admin_user.id

        if priority and priority != complaint.priority:
            comment_parts.append(f"Priority changed from {complaint.priority.value} to {priority.value}")
            complaint.priority = priority

        if status and status != complaint.status:
            if status not in ALLOWED_TRANSITIONS.get(complaint.status, []):
                raise InvalidStateTransitionException(complaint.status.value, status.value)
            comment_parts.append(f"Status changed from {complaint.status.value} to {status.value}")
            complaint.status = status
            if status == ComplaintStatus.RESOLVED:
                complaint.resolved_at = datetime.now(timezone.utc)

        if comment_parts:
            self.db.add(
                ComplaintTimeline(
                    complaint_id=complaint.id,
                    actor_id=admin_user.id,
                    action="ADMIN_UPDATE",
                    previous_status=current_status.value,
                    new_status=complaint.status.value,
                    comment="; ".join(comment_parts),
                )
            )

        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def submit_feedback(self, complaint_id: int, student: User, feedback_in: FeedbackCreate) -> ComplaintFeedback:
        complaint = self.repo.get_by_id(complaint_id)
        if not complaint:
            raise EntityNotFoundException("Complaint", complaint_id)

        if complaint.student_id != student.id:
            raise ForbiddenOperationException("You can only submit feedback for your own complaints.")

        if complaint.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            raise ForbiddenOperationException("Feedback can only be submitted after complaint resolution.")

        existing = self.activity_repo.get_feedback(complaint_id)
        if existing:
            raise ForbiddenOperationException("Feedback has already been submitted for this complaint.")

        feedback = ComplaintFeedback(
            complaint_id=complaint_id,
            student_id=student.id,
            staff_id=self.db.query(StaffAssignment.staff_id).filter(
                StaffAssignment.complaint_id == complaint_id,
                StaffAssignment.status == AssignmentStatus.COMPLETED,
            ).order_by(StaffAssignment.completed_at.desc()).limit(1).scalar(),
            rating=feedback_in.rating,
            comments=feedback_in.comments,
        )
        self.db.add(feedback)
        feedback.reward_points_awarded = 5 if self._award_points(student, complaint, 5, "RESOLUTION_FEEDBACK") else 0
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def _award_points(self, student: User, complaint: Complaint, points: int, reason: str) -> bool:
        """Write point ledger and balance together; unique key prevents duplicate awards."""
        if reason == "ISSUE_REPORTED":
            from datetime import timedelta
            from app.core.config import settings
            since = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(tzinfo=None)
            awarded_last_day = self.db.query(func.coalesce(func.sum(RewardTransaction.points), 0)).filter(
                RewardTransaction.student_id == student.id,
                RewardTransaction.reason == reason,
                RewardTransaction.created_at >= since,
            ).scalar() or 0
            if awarded_last_day + points > settings.DAILY_ISSUE_REWARD_LIMIT:
                return False
        transaction = RewardTransaction(
            student_id=student.id,
            complaint_id=complaint.id,
            points=points,
            reason=reason,
        )
        self.db.add(transaction)
        student.reward_points = (student.reward_points or 0) + points
        return True
