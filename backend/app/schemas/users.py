from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

ProfileItem = Annotated[
    str,
    Field(
        min_length=1,
        max_length=80,
    ),
]


def normalize_profile_items(
    values: list[str] | None,
) -> list[str] | None:
    if values is None:
        return None

    normalized: list[str] = []
    seen: set[str] = set()

    for value in values:
        item = " ".join(value.split())

        if not item:
            continue

        key = item.casefold()

        if key in seen:
            continue

        seen.add(key)
        normalized.append(item)

    return normalized


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = " ".join(value.split())

        if len(normalized) < 2:
            raise ValueError("Full name must contain at least two characters.")

        return normalized

    @model_validator(mode="after")
    def require_update_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one user field must be provided.")

        return self


class ProfileCreateRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    headline: str | None = Field(
        default=None,
        max_length=160,
    )
    location: str | None = Field(
        default=None,
        max_length=120,
    )
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=32,
        pattern=r"^\+?[0-9 ()-]+$",
    )
    bio: str | None = Field(
        default=None,
        max_length=2000,
    )
    years_experience: int | None = Field(
        default=None,
        ge=0,
        le=80,
    )
    target_roles: list[ProfileItem] = Field(
        default_factory=list,
        max_length=30,
    )
    skills: list[ProfileItem] = Field(
        default_factory=list,
        max_length=100,
    )
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None

    @field_validator(
        "target_roles",
        "skills",
    )
    @classmethod
    def normalize_lists(
        cls,
        value: list[str],
    ) -> list[str]:
        result = normalize_profile_items(value)

        if result is None:
            return []

        return result


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    headline: str | None = Field(
        default=None,
        max_length=160,
    )
    location: str | None = Field(
        default=None,
        max_length=120,
    )
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=32,
        pattern=r"^\+?[0-9 ()-]+$",
    )
    bio: str | None = Field(
        default=None,
        max_length=2000,
    )
    years_experience: int | None = Field(
        default=None,
        ge=0,
        le=80,
    )
    target_roles: list[ProfileItem] | None = Field(
        default=None,
        max_length=30,
    )
    skills: list[ProfileItem] | None = Field(
        default=None,
        max_length=100,
    )
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None

    @field_validator(
        "target_roles",
        "skills",
    )
    @classmethod
    def normalize_optional_lists(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        return normalize_profile_items(value)

    @model_validator(mode="after")
    def require_update_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one profile field must be provided.")

        return self


class ProfileResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user_id: UUID
    headline: str | None
    location: str | None
    phone: str | None
    bio: str | None
    years_experience: int | None
    target_roles: list[str]
    skills: list[str]
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    created_at: datetime
    updated_at: datetime
