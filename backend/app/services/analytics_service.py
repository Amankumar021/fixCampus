from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from sqlalchemy.sql import extract
from app.models.complaint import Complaint, ComplaintStatus
from app.models.assignment import StaffAssignment, AssignmentStatus
from app.models.activity import ComplaintFeedback
from app.models.user import User, UserRole
from datetime import datetime, timedelta, timezone
from app.core.config import settings


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_admin_metrics(self) -> Dict[str, Any]:
        total_complaints = self.db.query(Complaint).count()
        pending_complaints = self.db.query(Complaint).filter(Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW])).count()
        in_progress_complaints = self.db.query(Complaint).filter(Complaint.status.in_([ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS])).count()
        resolved_complaints = self.db.query(Complaint).filter(Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])).count()

        # Category distribution
        category_counts = (
            self.db.query(Complaint.category, func.count(Complaint.id))
            .group_by(Complaint.category)
            .all()
        )
        category_distribution = {cat: count for cat, count in category_counts}

        # Status distribution
        status_counts = (
            self.db.query(Complaint.status, func.count(Complaint.id))
            .group_by(Complaint.status)
            .all()
        )
        status_distribution = {status.value if hasattr(status, "value") else str(status): count for status, count in status_counts}

        # Average resolution time in hours
        resolved_records = (
            self.db.query(Complaint.created_at, Complaint.resolved_at)
            .filter(Complaint.resolved_at.isnot(None))
            .all()
        )
        avg_res_time_hours = 0.0
        if resolved_records:
            total_seconds = sum((res - created).total_seconds() for created, res in resolved_records if res and created)
            avg_res_time_hours = round(total_seconds / (len(resolved_records) * 3600), 1)

        # Average feedback rating
        avg_rating = self.db.query(func.avg(ComplaintFeedback.rating)).scalar() or 0.0

        # Staff performance count
        staff_performance = (
            self.db.query(
                User.full_name,
                User.department,
                func.count(StaffAssignment.id).label("total_assigned"),
                func.sum(case((StaffAssignment.status == AssignmentStatus.COMPLETED, 1), else_=0)).label("completed"),
            )
            .join(StaffAssignment, User.id == StaffAssignment.staff_id)
            .group_by(User.id)
            .all()
        )

        monthly_counts = (
            self.db.query(
                extract("year", Complaint.created_at).label("year"),
                extract("month", Complaint.created_at).label("month"),
                func.count(Complaint.id),
            )
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        pending_cutoff = now - timedelta(hours=settings.PENDING_ASSIGNMENT_OVERDUE_HOURS)
        active_cutoff = now - timedelta(hours=settings.ACTIVE_ASSIGNMENT_OVERDUE_HOURS)
        pending_rows = self.db.query(StaffAssignment, User, Complaint).join(
            User, User.id == StaffAssignment.staff_id
        ).join(Complaint, Complaint.id == StaffAssignment.complaint_id).filter(
            StaffAssignment.status == AssignmentStatus.PENDING,
            StaffAssignment.assigned_at <= pending_cutoff,
        ).all()
        active_rows = self.db.query(StaffAssignment, User, Complaint).join(
            User, User.id == StaffAssignment.staff_id
        ).join(Complaint, Complaint.id == StaffAssignment.complaint_id).filter(
            StaffAssignment.status == AssignmentStatus.ACCEPTED,
            StaffAssignment.responded_at.isnot(None),
            StaffAssignment.responded_at <= active_cutoff,
        ).all()
        overdue_work = []
        for assignment, staff, complaint in pending_rows:
            hours = (now - (assignment.assigned_at.replace(tzinfo=None) if assignment.assigned_at.tzinfo else assignment.assigned_at)).total_seconds() / 3600
            overdue_work.append({"ticket_id": complaint.ticket_id, "staff_name": staff.full_name,
                "department": staff.department, "assignment_status": "PENDING",
                "hours_overdue": round(hours - settings.PENDING_ASSIGNMENT_OVERDUE_HOURS, 1)})
        for assignment, staff, complaint in active_rows:
            hours = (now - (assignment.responded_at.replace(tzinfo=None) if assignment.responded_at.tzinfo else assignment.responded_at)).total_seconds() / 3600
            overdue_work.append({"ticket_id": complaint.ticket_id, "staff_name": staff.full_name,
                "department": staff.department, "assignment_status": "ACCEPTED",
                "hours_overdue": round(hours - settings.ACTIVE_ASSIGNMENT_OVERDUE_HOURS, 1)})
        overdue_work.sort(key=lambda item: item["hours_overdue"], reverse=True)

        return {
            "total_complaints": total_complaints,
            "pending_complaints": pending_complaints,
            "in_progress_complaints": in_progress_complaints,
            "resolved_complaints": resolved_complaints,
            "overdue_assignments": len(overdue_work),
            "overdue_work": overdue_work,
            "avg_resolution_hours": avg_res_time_hours,
            "avg_feedback_rating": round(float(avg_rating), 1),
            "category_distribution": category_distribution,
            "status_distribution": status_distribution,
            "monthly_complaints": [
                {"year": int(year), "month": int(month), "count": count}
                for year, month, count in monthly_counts
            ],
            "staff_metrics": [
                {
                    "staff_name": name,
                    "department": dept,
                    "total_assigned": total,
                    "completed": completed or 0,
                }
                for name, dept, total, completed in staff_performance
            ],
        }
