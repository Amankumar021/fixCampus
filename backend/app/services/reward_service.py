from sqlalchemy.orm import Session
from app.core.exceptions import ForbiddenOperationException
from app.models.reward import RewardTransaction
from app.models.user import User, UserRole


class RewardService:
    def __init__(self, db: Session):
        self.db = db

    def get_student_rewards(self, student: User):
        if student.role != UserRole.STUDENT:
            raise ForbiddenOperationException("Student rewards are available only to student accounts.")
        transactions = (
            self.db.query(RewardTransaction)
            .filter(RewardTransaction.student_id == student.id)
            .order_by(RewardTransaction.created_at.desc(), RewardTransaction.id.desc())
            .limit(50)
            .all()
        )
        points = student.reward_points or 0
        milestone = ((points // 50) + 1) * 50
        return {
            "total_points": points,
            "next_milestone": milestone,
            "points_to_next_milestone": milestone - points,
            "transactions": transactions,
        }
