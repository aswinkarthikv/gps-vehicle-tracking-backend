from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.tracking import router as tracking_router
from app.api.gps import router as gps_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(tracking_router)
api_router.include_router(gps_router)
