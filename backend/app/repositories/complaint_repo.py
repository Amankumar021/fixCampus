from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from app.models.assignment import StaffAssignment


class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, complaint_id: int) -> Optional[Complaint]:
        return (
            self.db.query(Complaint)
            .options(joinedload(Complaint.student))
            .filter(Complaint.id == complaint_id)
            .first()
        )

    def get_by_ticket_id(self, ticket_id: str) -> Optional[Complaint]:
        return (
            self.db.query(Complaint)
            .options(joinedload(Complaint.student))
            .filter(Complaint.ticket_id == ticket_id)
            .first()
        )

    def get_all(
        self,
        status: Optional[ComplaintStatus] = None,
        category: Optional[str] = None,
        priority: Optional[ComplaintPriority] = None,
        student_id: Optional[int] = None,
        staff_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Complaint]:
        query = self.db.query(Complaint).options(joinedload(Complaint.student))
        if status:
            query = query.filter(Complaint.status == status)
        if category:
            query = query.filter(Complaint.category == category)
        if priority:
            query = query.filter(Complaint.priority == priority)
        if student_id:
            query = query.filter(Complaint.student_id == student_id)
        if staff_id:
            query = query.join(StaffAssignment).filter(StaffAssignment.staff_id == staff_id)

        return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    def count(
        self,
        status: Optional[ComplaintStatus] = None,
        category: Optional[str] = None,
        student_id: Optional[int] = None,
    ) -> int:
        query = self.db.query(Complaint)
        if status:
            query = query.filter(Complaint.status == status)
        if category:
            query = query.filter(Complaint.category == category)
        if student_id:
            query = query.filter(Complaint.student_id == student_id)
        return query.count()

    def create(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def update(self, complaint: Complaint) -> Complaint:
        self.db.commit()
        self.db.refresh(complaint)
        return complaint
