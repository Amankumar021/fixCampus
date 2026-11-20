from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole
from app.models.complaint import ComplaintStatus, ComplaintPriority


# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetMessage(BaseModel):
    message: str


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.STUDENT
    department: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    phone_number: Optional[str] = None
    # Public registration deliberately has no role field.


class StaffCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    department: str
    phone_number: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    department: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    reward_points: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Complaint Schemas
class ComplaintCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    location: str = Field(min_length=2, max_length=150)
    category: Optional[str] = None # Optional; if omitted, AI will predict
    priority: Optional[ComplaintPriority] = ComplaintPriority.MEDIUM
    attachment_url: Optional[str] = Field(default=None, max_length=300)


class ComplaintUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[ComplaintPriority] = None
    status: Optional[ComplaintStatus] = None


class ComplaintResponse(BaseModel):
    id: int
    ticket_id: str
    title: str
    description: str
    location: str
    category: str
    predicted_category: Optional[str] = None
    prediction_confidence: Optional[float] = None
    is_category_overridden: bool
    priority: ComplaintPriority
    report_count: int = 1
    status: ComplaintStatus
    attachment_url: Optional[str] = None
    student_id: int
    student: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    reward_points_awarded: int = 0

    model_config = ConfigDict(from_attributes=True)


# Assignment Schemas
class AssignmentCreate(BaseModel):
    complaint_id: int
    staff_id: int


class AssignmentResponse(BaseModel):
    id: int
    complaint_id: int
    staff_id: int
    assigned_by_id: int
    status: str
    rejection_reason: Optional[str] = None
    resolution_notes: Optional[str] = None
    assigned_at: datetime
    responded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    staff: Optional[UserResponse] = None
    complaint: Optional[ComplaintResponse] = None

    model_config = ConfigDict(from_attributes=True)


# Timeline & Feedback Schemas
class TimelineResponse(BaseModel):
    id: int
    complaint_id: int
    actor_id: int
    action: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    actor: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    complaint_id: int
    student_id: int
    staff_id: Optional[int] = None
    staff: Optional[UserResponse] = None
    complaint: Optional[ComplaintResponse] = None
    rating: int
    comments: Optional[str] = None
    created_at: datetime
    reward_points_awarded: int = 0

    model_config = ConfigDict(from_attributes=True)


class RewardTransactionResponse(BaseModel):
    id: int
    complaint_id: int
    points: int
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentRewardsResponse(BaseModel):
    total_points: int
    next_milestone: int
    points_to_next_milestone: int
    transactions: List[RewardTransactionResponse]


# ML Inference Schema
class MLPredictRequest(BaseModel):
    description: str = Field(min_length=5, max_length=5000)


class MLPredictResponse(BaseModel):
    predicted_category: str
    confidence: float
    is_confident: bool
    method: str
