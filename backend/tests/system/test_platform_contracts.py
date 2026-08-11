"""Platform-wide contracts protecting agentic architecture."""

from __future__ import annotations

from app.orchestration.real_agents import (
    load_real_agent_workflows,
)
from app.orchestration.state import (
    CORE_PIPELINE_ORDER,
)
from app.prompts.management import (
    get_default_prompt_manager,
)
from app.tool_calling.runtime import (
    build_default_tool_runtime,
)


def test_real_workflow_modules_import() -> None:
    """Every core production agent workflow is importable."""

    workflows = load_real_agent_workflows()

    assert callable(workflows.resume_parser)

    assert callable(workflows.job_description_analyzer)

    assert callable(workflows.resume_matching)

    assert callable(workflows.ats_optimization)

    assert callable(workflows.skill_gap)

    assert callable(workflows.cover_letter)


def test_core_agent_prompts_are_registered() -> None:
    """Every prompt-driven core agent has managed prompts."""

    manager = get_default_prompt_manager()

    for agent_name in CORE_PIPELINE_ORDER:
        prompt = manager.resolve(agent_name)

        assert prompt.version

        assert len(prompt.checksum) == 64

        assert prompt.system_prompt

        assert prompt.user_prompt


def test_tool_permissions_reference_real_tools() -> None:
    """Agent permissions never reference unknown tools."""

    runtime = build_default_tool_runtime()

    registered = set(runtime.registry.names())

    for agent_name in CORE_PIPELINE_ORDER:
        allowed = set(runtime.tool_names_for_agent(agent_name))

        assert allowed <= registered


def test_core_pipeline_has_unique_nodes() -> None:
    """Central execution order must never contain duplicates."""

    assert len(CORE_PIPELINE_ORDER) == len(set(CORE_PIPELINE_ORDER))


def test_expected_core_pipeline_contract() -> None:
    """Protect intended multi-agent orchestration order."""

    assert list(CORE_PIPELINE_ORDER) == [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
        "ats_optimization",
        "skill_gap",
        "cover_letter",
    ]
