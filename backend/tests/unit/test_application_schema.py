from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
)


def test_create_application_schema() -> None:
    payload = ApplicationCreateRequest(
        company="Google",
        role="Software Engineer",
        location="Bengaluru",
        applied_at=date(
            2026,
            8,
            13,
        ),
        status="applied",
        notes="Referral application",
    )

    assert payload.company == "Google"

    assert payload.role == "Software Engineer"


def test_create_application_rejects_empty_company() -> None:
    with pytest.raises(ValidationError):
        ApplicationCreateRequest(
            company="   ",
            role="Engineer",
        )


def test_invalid_application_status() -> None:
    with pytest.raises(ValidationError):
        ApplicationCreateRequest.model_validate(
            {
                "company": "Google",
                "role": "Engineer",
                "status": "unknown",
            }
        )


def test_update_application_partial() -> None:
    payload = ApplicationUpdateRequest(status="interview")

    assert payload.model_dump(exclude_unset=True) == {"status": "interview"}
