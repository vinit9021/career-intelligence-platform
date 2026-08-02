import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    email: EmailStr
    password: str = Field(
        min_length=12,
        max_length=128,
    )
    full_name: str = Field(
        min_length=2,
        max_length=120,
    )

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:
        checks = (
            (
                r"[a-z]",
                "one lowercase letter",
            ),
            (
                r"[A-Z]",
                "one uppercase letter",
            ),
            (
                r"\d",
                "one digit",
            ),
            (
                r"[^A-Za-z0-9]",
                "one special character",
            ),
        )

        if any(character.isspace() for character in value):
            raise ValueError("Password must not contain whitespace.")

        missing = [message for pattern, message in checks if re.search(pattern, value) is None]

        if missing:
            raise ValueError("Password must contain " + ", ".join(missing) + ".")

        return value

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(
        cls,
        value: str,
    ) -> str:
        normalized = " ".join(value.split())

        if len(normalized) < 2:
            raise ValueError("Full name must contain at least two characters.")

        return normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        min_length=20,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class ErrorResponse(BaseModel):
    detail: str
