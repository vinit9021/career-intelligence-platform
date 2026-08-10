"""Tests for LangChain tool integration."""

from app.tool_calling.runtime import (
    build_default_tool_runtime,
)


def test_matching_agent_gets_allowed_tools() -> None:
    runtime = build_default_tool_runtime()

    tools = runtime.tools_for_agent("resume_matching")

    names = {tool.name for tool in tools}

    assert names == {
        "evidence_lookup",
        "keyword_overlap",
    }


def test_cover_letter_has_restricted_tools() -> None:
    runtime = build_default_tool_runtime()

    assert runtime.tool_names_for_agent("cover_letter") == ["evidence_lookup"]


def test_unknown_agent_gets_no_tools() -> None:
    runtime = build_default_tool_runtime()

    assert runtime.tool_names_for_agent("unknown_agent") == []
