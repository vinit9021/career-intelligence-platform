from typing import Annotated

from fastapi import Depends

from app.api.dependencies.resumes import DbSession, StorageDependency
from app.services.resume_library import ResumeLibraryService


def get_resume_library_service(
    session: DbSession,
    storage: StorageDependency,
) -> ResumeLibraryService:
    return ResumeLibraryService(
        session=session,
        storage=storage,
    )


ResumeLibraryServiceDependency = Annotated[
    ResumeLibraryService,
    Depends(get_resume_library_service),
]
