import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class StaffAssignment(Base):
    __tablename__ = "staff_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    complaint_id: Mapped[int] = mapped_column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    status: Mapped[AssignmentStatus] = mapped_column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING, nullable=False, index=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    responded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    complaint = relationship("Complaint", back_populates="assignments")
    staff = relationship("User", foreign_keys=[staff_id], back_populates="assigned_tasks")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
