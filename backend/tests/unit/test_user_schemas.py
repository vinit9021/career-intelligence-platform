import pytest
from pydantic import ValidationError

from app.schemas.users import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    UserUpdateRequest,
)


def test_user_name_is_normalized() -> None:
    payload = UserUpdateRequest(full_name="  Alice   Example  ")

    assert payload.full_name == "Alice Example"


def test_empty_user_update_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UserUpdateRequest()


def test_profile_lists_are_normalized() -> None:
    payload = ProfileCreateRequest(
        target_roles=[
            " Backend Engineer ",
            "backend engineer",
            "AI Engineer",
        ],
        skills=[
            " Python ",
            "python",
            "FastAPI",
        ],
    )

    assert payload.target_roles == [
        "Backend Engineer",
        "AI Engineer",
    ]

    assert payload.skills == [
        "Python",
        "FastAPI",
    ]


def test_empty_profile_update_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdateRequest()


def test_invalid_experience_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileCreateRequest(years_experience=81)
