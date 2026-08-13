from app.api.dependencies.applications import ApplicationServiceDependency, get_application_service
from app.api.dependencies.auth import CurrentUser, get_auth_service, get_current_user
from app.api.dependencies.resumes import (
    ResumeParsingServiceDependency,
    ResumeServiceDependency,
    get_parser_registry,
    get_resume_parsing_service,
    get_resume_service,
    get_storage_backend,
)
from app.api.dependencies.users import UserServiceDependency, get_user_service

__all__ = [
    "ApplicationServiceDependency",
    "CurrentUser",
    "ResumeParsingServiceDependency",
    "ResumeServiceDependency",
    "UserServiceDependency",
    "get_application_service",
    "get_auth_service",
    "get_current_user",
    "get_parser_registry",
    "get_resume_parsing_service",
    "get_resume_service",
    "get_storage_backend",
    "get_user_service",
]
