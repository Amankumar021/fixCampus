import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True) # E.g., Electrical, IT, Plumbing for staff
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    complaints = relationship("Complaint", back_populates="student", foreign_keys="Complaint.student_id")
    assigned_tasks = relationship("StaffAssignment", back_populates="staff", foreign_keys="StaffAssignment.staff_id")
