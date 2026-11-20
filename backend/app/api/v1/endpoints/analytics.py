from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.analytics_service import AnalyticsService
from app.dependencies.auth import require_admin
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=Dict[str, Any])
def get_analytics_overview(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = AnalyticsService(db)
    return service.get_admin_metrics()
