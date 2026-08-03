from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.parsers import ResumeParserRegistry, build_default_parser_registry
from app.services.resume_parsing import ResumeParsingService
from app.services.resumes import ResumeService
from app.storage import ObjectStorage, build_storage

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_storage_backend(settings: SettingsDependency) -> ObjectStorage:
    return build_storage(settings)


StorageDependency = Annotated[ObjectStorage, Depends(get_storage_backend)]


def get_parser_registry() -> ResumeParserRegistry:
    return build_default_parser_registry()


ParserRegistryDependency = Annotated[
    ResumeParserRegistry,
    Depends(get_parser_registry),
]


def get_resume_service(
    session: DbSession,
    storage: StorageDependency,
    settings: SettingsDependency,
) -> ResumeService:
    return ResumeService(
        session=session,
        storage=storage,
        max_size_bytes=settings.resume_max_size_bytes,
    )


ResumeServiceDependency = Annotated[ResumeService, Depends(get_resume_service)]


def get_resume_parsing_service(
    session: DbSession,
    storage: StorageDependency,
    parser_registry: ParserRegistryDependency,
) -> ResumeParsingService:
    return ResumeParsingService(
        session=session,
        storage=storage,
        parser_registry=parser_registry,
    )


ResumeParsingServiceDependency = Annotated[
    ResumeParsingService,
    Depends(get_resume_parsing_service),
]
