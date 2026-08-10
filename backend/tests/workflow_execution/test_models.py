"""Tests for workflow execution models."""

import pytest
from pydantic import ValidationError

from app.workflow_execution.models import (
    WorkflowExecutionRequest,
)


def test_request_rejects_blank_resume() -> None:
    with pytest.raises(ValidationError):
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="s1",
            resume_raw_text="   ",
            job_description_text="JD",
        )


def test_request_rejects_duplicate_nodes() -> None:
    with pytest.raises(ValidationError):
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="s1",
            resume_raw_text="Resume",
            job_description_text="JD",
            enabled_nodes=[
                "resume_parser",
                "resume_parser",
            ],
        )


def test_request_requires_at_least_one_node() -> None:
    with pytest.raises(ValidationError):
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="s1",
            resume_raw_text="Resume",
            job_description_text="JD",
            enabled_nodes=[],
        )
