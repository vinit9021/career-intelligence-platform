"""Tests for memory write policy."""

import pytest

from app.memory.models import (
    MemoryRecord,
)
from app.memory.policy import (
    MemoryPolicy,
    MemoryPolicyError,
)


def test_short_term_requires_session() -> None:
    record = MemoryRecord(
        user_id="u1",
        scope="short_term",
        namespace="workflow",
        key="state",
        value={"step": 1},
    )

    with pytest.raises(MemoryPolicyError):
        MemoryPolicy().validate(record)


def test_workflow_cannot_be_long_term() -> None:
    record = MemoryRecord(
        user_id="u1",
        scope="long_term",
        namespace="workflow",
        key="result",
        value={"status": "done"},
    )

    with pytest.raises(MemoryPolicyError):
        MemoryPolicy().validate(record)


def test_sensitive_key_is_rejected() -> None:
    record = MemoryRecord(
        user_id="u1",
        scope="long_term",
        namespace="user_preferences",
        key="api_key",
        value="hidden",
    )

    with pytest.raises(MemoryPolicyError):
        MemoryPolicy().validate(record)


def test_nested_secret_is_rejected() -> None:
    record = MemoryRecord(
        user_id="u1",
        scope="long_term",
        namespace="user_preferences",
        key="settings",
        value={
            "theme": "dark",
            "password": "hidden",
        },
    )

    with pytest.raises(MemoryPolicyError):
        MemoryPolicy().validate(record)


def test_valid_long_term_memory() -> None:
    record = MemoryRecord(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="Backend Engineer",
    )

    MemoryPolicy().validate(record)
