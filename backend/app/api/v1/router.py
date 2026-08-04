from fastapi import APIRouter

from app.api.v1.auth import (
    router as auth_router,
)
from app.api.v1.health import (
    router as health_router,
)
from app.api.v1.resume_library import router as resume_library_router
from app.api.v1.resumes import (
    router as resumes_router,
)
from app.api.v1.users import (
    router as users_router,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(resume_library_router)
