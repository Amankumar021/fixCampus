from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ComplaintTimeline(Base):
    __tablename__ = "complaint_timelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    complaint_id: Mapped[int] = mapped_column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "STATUS_CHANGE", "ASSIGNED", "NOTE_ADDED"
    previous_status: Mapped[str] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="timeline_logs")
    actor = relationship("User", foreign_keys=[actor_id])


class ComplaintFeedback(Base):
    __tablename__ = "complaint_feedbacks"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    complaint_id: Mapped[int] = mapped_column(Integer, ForeignKey("complaints.id"), unique=True, nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    rating: Mapped[int] = mapped_column(Integer, nullable=False) # 1 to 5
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="feedback")
    student = relationship("User", foreign_keys=[student_id])
    staff = relationship("User", foreign_keys=[staff_id])
