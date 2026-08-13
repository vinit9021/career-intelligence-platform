from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)

ApplicationStatus = Literal[
    "applied",
    "online_assessment",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
]

ApplicationSource = Literal[
    "manual",
    "gmail",
    "integration",
]

ApplicationSortField = Literal[
    "applied_at",
    "created_at",
    "company",
    "role",
    "status",
]

SortOrder = Literal[
    "asc",
    "desc",
]


class ApplicationCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(
        min_length=1,
        max_length=160,
    )

    role: str = Field(
        min_length=1,
        max_length=200,
    )

    job_url: HttpUrl | None = None

    location: str | None = Field(
        default=None,
        max_length=160,
    )

    applied_at: date = Field(default_factory=date.today)

    status: ApplicationStatus = "applied"

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


class ApplicationUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )

    role: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    job_url: HttpUrl | None = None

    location: str | None = Field(
        default=None,
        max_length=160,
    )

    applied_at: date | None = None

    status: ApplicationStatus | None = None

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: str
    role: str
    job_url: str | None
    location: str | None
    applied_at: date
    status: ApplicationStatus
    source: ApplicationSource
    external_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationPageResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
    page: int
    page_size: int
