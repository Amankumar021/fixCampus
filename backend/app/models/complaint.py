import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum, Text, ForeignKey, Float, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"


class ComplaintPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplaintCategory(str, enum.Enum):
    ELECTRICAL = "Electrical"
    IT = "IT"
    PLUMBING = "Plumbing"
    CLEANLINESS = "Cleanliness"
    SECURITY = "Security"
    FURNITURE = "Furniture"
    CIVIL_MAINTENANCE = "Civil Maintenance"
    SANITATION = "Sanitation"
    CAFETERIA = "Cafeteria"
    OTHER = "Other"


def generate_ticket_number():
    return f"CFX-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (Index("ix_complaints_status_created", "status", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, default=generate_ticket_number)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # Category (AI predicted or Admin overridden)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    predicted_category: Mapped[str] = mapped_column(String(100), nullable=True)
    prediction_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    is_category_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    category_reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    category_reviewed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    priority: Mapped[ComplaintPriority] = mapped_column(Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM, nullable=False, index=True)
    report_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus), default=ComplaintStatus.SUBMITTED, nullable=False, index=True)

    # Attachments
    attachment_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Foreign Keys
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    student = relationship("User", back_populates="complaints", foreign_keys=[student_id])
    assignments = relationship("StaffAssignment", back_populates="complaint", cascade="all, delete-orphan")
    timeline_logs = relationship("ComplaintTimeline", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintTimeline.created_at.asc()")
    feedback = relationship("ComplaintFeedback", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
