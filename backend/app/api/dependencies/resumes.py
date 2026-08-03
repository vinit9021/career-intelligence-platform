from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.config import (
    Settings,
    get_settings,
)
from app.db.session import get_db_session
from app.services.resumes import (
    ResumeService,
)
from app.storage import (
    ObjectStorage,
    build_storage,
)

DbSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]

SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]


def get_storage_backend(
    settings: SettingsDependency,
) -> ObjectStorage:
    return build_storage(settings)


StorageDependency = Annotated[
    ObjectStorage,
    Depends(get_storage_backend),
]


def get_resume_service(
    session: DbSession,
    storage: StorageDependency,
    settings: SettingsDependency,
) -> ResumeService:
    return ResumeService(
        session=session,
        storage=storage,
        max_size_bytes=(settings.resume_max_size_bytes),
    )


ResumeServiceDependency = Annotated[
    ResumeService,
    Depends(get_resume_service),
]
