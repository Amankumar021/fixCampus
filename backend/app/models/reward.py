from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RewardTransaction(Base):
    __tablename__ = "reward_transactions"
    __table_args__ = (
        CheckConstraint("points > 0", name="ck_reward_points_positive"),
        UniqueConstraint("student_id", "complaint_id", "reason", name="uq_reward_student_complaint_reason"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), nullable=False, index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(48), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("User")
    complaint = relationship("Complaint")
