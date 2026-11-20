from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.schemas import StudentRewardsResponse
from app.services.reward_service import RewardService

router = APIRouter(prefix="/rewards", tags=["Student Rewards"])


@router.get("/me", response_model=StudentRewardsResponse)
def get_my_rewards(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return RewardService(db).get_student_rewards(current_user)
