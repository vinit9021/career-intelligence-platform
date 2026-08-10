"""Tests for tool permissions."""

from app.tool_calling.permissions import (
    ToolPermissionPolicy,
)


def test_allowed_tool() -> None:
    policy = ToolPermissionPolicy({"resume_matching": {"keyword_overlap"}})

    assert policy.is_allowed(
        agent_name="resume_matching",
        tool_name="keyword_overlap",
    )


def test_denied_tool() -> None:
    policy = ToolPermissionPolicy({"resume_parser": {"evidence_lookup"}})

    assert not policy.is_allowed(
        agent_name="resume_parser",
        tool_name="keyword_overlap",
    )


def test_wildcard_permission() -> None:
    policy = ToolPermissionPolicy({"admin_agent": {"*"}})

    assert policy.is_allowed(
        agent_name="admin_agent",
        tool_name="any_tool",
    )


def test_grant_and_revoke() -> None:
    policy = ToolPermissionPolicy()

    policy.grant(
        agent_name="agent",
        tool_name="tool_a",
    )

    assert policy.is_allowed(
        agent_name="agent",
        tool_name="tool_a",
    )

    policy.revoke(
        agent_name="agent",
        tool_name="tool_a",
    )

    assert not policy.is_allowed(
        agent_name="agent",
        tool_name="tool_a",
    )
