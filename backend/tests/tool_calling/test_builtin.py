"""Tests for built-in career tools."""

import pytest

from app.tool_calling.builtin import (
    build_builtin_tool_registry,
)
from app.tool_calling.executor import (
    ToolExecutor,
)
from app.tool_calling.models import (
    ToolCallRequest,
)
from app.tool_calling.permissions import (
    ToolPermissionPolicy,
)


@pytest.mark.asyncio
async def test_evidence_lookup() -> None:
    registry = build_builtin_tool_registry()

    executor = ToolExecutor(
        registry=registry,
        permissions=(ToolPermissionPolicy({"agent": {"evidence_lookup"}})),
    )

    result = await executor.execute(
        agent_name="agent",
        request=ToolCallRequest(
            tool_name="evidence_lookup",
            arguments={
                "text": ("Built APIs using FastAPI and PostgreSQL."),
                "query": "FastAPI",
                "context_chars": 20,
            },
        ),
    )

    assert result.status == "success"

    assert result.output["found"] is True


@pytest.mark.asyncio
async def test_keyword_overlap() -> None:
    registry = build_builtin_tool_registry()

    executor = ToolExecutor(
        registry=registry,
        permissions=(ToolPermissionPolicy({"agent": {"keyword_overlap"}})),
    )

    result = await executor.execute(
        agent_name="agent",
        request=ToolCallRequest(
            tool_name="keyword_overlap",
            arguments={
                "resume_keywords": [
                    "Python",
                    "FastAPI",
                ],
                "job_keywords": [
                    "Python",
                    "Docker",
                ],
            },
        ),
    )

    assert result.status == "success"

    assert result.output["matched_keywords"] == ["python"]

    assert result.output["missing_keywords"] == ["docker"]

    assert result.output["match_percentage"] == 50.0
