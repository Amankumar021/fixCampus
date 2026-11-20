from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.models.assignment import StaffAssignment, AssignmentStatus
from app.models.activity import ComplaintTimeline, ComplaintFeedback


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, assignment_id: int) -> Optional[StaffAssignment]:
        return (
            self.db.query(StaffAssignment)
            .options(joinedload(StaffAssignment.complaint), joinedload(StaffAssignment.staff))
            .filter(StaffAssignment.id == assignment_id)
            .first()
        )

    def get_by_complaint(self, complaint_id: int) -> List[StaffAssignment]:
        return (
            self.db.query(StaffAssignment)
            .options(joinedload(StaffAssignment.staff))
            .filter(StaffAssignment.complaint_id == complaint_id)
            .order_by(StaffAssignment.assigned_at.desc())
            .all()
        )

    def get_by_staff(self, staff_id: int, status: Optional[AssignmentStatus] = None) -> List[StaffAssignment]:
        query = (
            self.db.query(StaffAssignment)
            .options(joinedload(StaffAssignment.complaint))
            .filter(StaffAssignment.staff_id == staff_id)
        )
        if status:
            query = query.filter(StaffAssignment.status == status)
        return query.order_by(StaffAssignment.assigned_at.desc()).all()

    def create(self, assignment: StaffAssignment) -> StaffAssignment:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def update(self, assignment: StaffAssignment) -> StaffAssignment:
        self.db.commit()
        self.db.refresh(assignment)
        return assignment


class ActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_timeline_entry(self, entry: ComplaintTimeline) -> ComplaintTimeline:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_timeline_by_complaint(self, complaint_id: int) -> List[ComplaintTimeline]:
        return (
            self.db.query(ComplaintTimeline)
            .options(joinedload(ComplaintTimeline.actor))
            .filter(ComplaintTimeline.complaint_id == complaint_id)
            .order_by(ComplaintTimeline.created_at.asc())
            .all()
        )

    def add_feedback(self, feedback: ComplaintFeedback) -> ComplaintFeedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_feedback(self, complaint_id: int) -> Optional[ComplaintFeedback]:
        return (self.db.query(ComplaintFeedback)
            .options(joinedload(ComplaintFeedback.staff), joinedload(ComplaintFeedback.complaint))
            .filter(ComplaintFeedback.complaint_id == complaint_id).first())

    def get_feedback_for_staff(self, staff_id: int) -> List[ComplaintFeedback]:
        return (self.db.query(ComplaintFeedback)
            .options(joinedload(ComplaintFeedback.complaint), joinedload(ComplaintFeedback.student))
            .filter(ComplaintFeedback.staff_id == staff_id)
            .order_by(ComplaintFeedback.created_at.desc()).all())
