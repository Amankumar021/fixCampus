from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.complaints import router as complaints_router
from app.api.v1.endpoints.staff import router as staff_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.ml import router as ml_router
from app.api.v1.endpoints.rewards import router as rewards_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(complaints_router)
api_v1_router.include_router(staff_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(rewards_router)
