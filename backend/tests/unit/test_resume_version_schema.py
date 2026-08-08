"""Tests for resume version schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)
from app.schemas.resume_version import (
    ResumeVersionCreate,
)


def build_resume() -> ResumeStructuredContent:
    return ResumeStructuredContent.model_validate(
        {
            "summary": "Backend engineer",
            "skills": [
                "Python",
                "FastAPI",
            ],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
        }
    )


def test_version_create_accepts_variant() -> None:
    request = ResumeVersionCreate(
        user_id=uuid4(),
        variant="backend",
        content=build_resume(),
        ats_score=88,
    )

    assert request.variant == "backend"
    assert request.ats_score == 88


def test_version_rejects_invalid_variant() -> None:
    with pytest.raises(ValidationError):
        ResumeVersionCreate.model_validate(
            {
                "user_id": str(uuid4()),
                "variant": "random",
                "content": (build_resume().model_dump(mode="json")),
            }
        )


def test_ats_score_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ResumeVersionCreate(
            user_id=uuid4(),
            variant="ai",
            content=build_resume(),
            ats_score=120,
        )
