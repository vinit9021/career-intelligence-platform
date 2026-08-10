"""Additional edge coverage for real-agent adapters."""

from __future__ import annotations

from types import ModuleType
from typing import Any, cast

import pytest
from pydantic import BaseModel

import app.orchestration.real_agents as real_agents
from app.orchestration.production import (
    run_real_career_workflow,
)
from app.orchestration.state import (
    AgentNodeName,
)


class RequestModel(BaseModel):
    value: int


async def noop_runner(
    **_: Any,
) -> dict[str, Any]:
    return {
        "status": "completed",
        "result": {},
    }


def build_noop_workflows(
    *,
    manager: (real_agents.WorkflowRunner | None) = None,
) -> real_agents.RealAgentWorkflows:
    return real_agents.RealAgentWorkflows(
        resume_parser=noop_runner,
        job_description_analyzer=(noop_runner),
        resume_matching=noop_runner,
        ats_optimization=noop_runner,
        skill_gap=noop_runner,
        cover_letter=noop_runner,
        resume_version_manager=manager,
    )


def test_load_runner_skips_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("working_module")

    vars(module)["wanted_runner"] = noop_runner

    def fake_import(
        name: str,
    ) -> ModuleType:
        if name == "broken_module":
            raise ImportError("broken import")

        return module

    monkeypatch.setattr(
        real_agents,
        "import_module",
        fake_import,
    )

    result = real_agents._load_runner(
        (
            "broken_module",
            "working_module",
        ),
        (
            "missing_runner",
            "wanted_runner",
        ),
    )

    assert result is noop_runner


def test_load_runner_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_import(
        _: str,
    ) -> ModuleType:
        raise ImportError("module unavailable")

    monkeypatch.setattr(
        real_agents,
        "import_module",
        fake_import,
    )

    with pytest.raises(
        ImportError,
        match="module unavailable",
    ):
        real_agents._load_runner(
            ("missing_module",),
            ("missing_runner",),
        )


def test_load_all_real_workflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[
        tuple[
            tuple[str, ...],
            tuple[str, ...],
        ]
    ] = []

    def fake_loader(
        modules: tuple[str, ...],
        names: tuple[str, ...],
    ) -> real_agents.WorkflowRunner:
        calls.append(
            (
                modules,
                names,
            )
        )

        return noop_runner

    monkeypatch.setattr(
        real_agents,
        "_load_runner",
        fake_loader,
    )

    workflows = real_agents.load_real_agent_workflows(include_resume_version_manager=True)

    assert len(calls) == 7

    assert workflows.resume_version_manager is noop_runner


def test_require_helper() -> None:
    assert (
        real_agents._require(
            "value",
            "error",
        )
        == "value"
    )

    with pytest.raises(
        ValueError,
        match="missing",
    ):
        real_agents._require(
            None,
            "missing",
        )

    with pytest.raises(
        ValueError,
        match="blank",
    ):
        real_agents._require(
            "   ",
            "blank",
        )


def test_type_hints_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_hints(
        _: Any,
    ) -> dict[str, Any]:
        raise NameError("bad annotation")

    monkeypatch.setattr(
        real_agents,
        "get_type_hints",
        fail_hints,
    )

    assert real_agents._type_hints(noop_runner) == {}


def test_is_pydantic_model_type_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_issubclass(
        *_: Any,
    ) -> bool:
        raise TypeError("bad type")

    monkeypatch.setattr(
        real_agents,
        "issubclass",
        fail_issubclass,
        raising=False,
    )

    assert real_agents._is_pydantic_model(RequestModel) is False


def test_argument_coercion() -> None:
    async def runner(
        *,
        request: RequestModel,
    ) -> dict[str, Any]:
        return {"value": request.value}

    typed_runner = cast(
        real_agents.WorkflowRunner,
        runner,
    )

    coerced = real_agents._coerce_argument(
        typed_runner,
        "request",
        {"value": 4},
    )

    assert isinstance(
        coerced,
        RequestModel,
    )

    assert coerced.value == 4

    same = RequestModel(value=5)

    assert (
        real_agents._coerce_argument(
            typed_runner,
            "request",
            same,
        )
        is same
    )


def test_build_request_model_rejects_non_model() -> None:
    async def runner(
        *,
        request: Any,
    ) -> dict[str, Any]:
        return {"request": request}

    with pytest.raises(
        TypeError,
        match="Pydantic request model",
    ):
        real_agents._build_request_model(
            cast(
                real_agents.WorkflowRunner,
                runner,
            ),
            "request",
            {"value": 1},
        )


@pytest.mark.asyncio
async def test_invoke_workflow_builds_request_model() -> None:
    async def runner(
        *,
        request: RequestModel,
    ) -> dict[str, Any]:
        return {"value": request.value}

    result = await real_agents._invoke_workflow(
        cast(
            real_agents.WorkflowRunner,
            runner,
        ),
        {"value": 8},
    )

    assert result == {"value": 8}


@pytest.mark.asyncio
async def test_invoke_workflow_uses_default() -> None:
    async def runner(
        *,
        value: int = 9,
    ) -> dict[str, Any]:
        return {"value": value}

    result = await real_agents._invoke_workflow(
        cast(
            real_agents.WorkflowRunner,
            runner,
        ),
        {},
    )

    assert result == {"value": 9}


@pytest.mark.asyncio
async def test_invoke_workflow_missing_required_argument() -> None:
    async def runner(
        *,
        value: int,
    ) -> dict[str, Any]:
        return {"value": value}

    with pytest.raises(
        ValueError,
        match="Missing required",
    ):
        await real_agents._invoke_workflow(
            cast(
                real_agents.WorkflowRunner,
                runner,
            ),
            {},
        )


def test_normalize_completed_result() -> None:
    result = real_agents._normalize_result(
        result={
            "status": ("completed_with_fallback"),
            "warnings": ["fallback used"],
            "result": {"value": 1},
        },
        output_fields=("result",),
    )

    assert result.status == "completed"

    assert result.output == {"value": 1}

    assert result.warnings == ["fallback used"]


def test_normalize_rejects_unsafe_output() -> None:
    result = real_agents._normalize_result(
        result={
            "status": "completed",
            "result": object(),
        },
        output_fields=("result",),
    )

    assert result.status == "failed"

    assert result.retryable is False

    assert result.error is not None


@pytest.mark.parametrize(
    (
        "payload",
        "expected",
    ),
    [
        (
            {
                "status": "failed",
                "last_error": ("explicit error"),
            },
            "explicit error",
        ),
        (
            {
                "status": "failed",
                "validation_errors": ["validation error"],
            },
            "validation error",
        ),
        (
            {
                "status": "failed",
            },
            ("Agent workflow returned status failed."),
        ),
    ],
)
def test_normalize_failed_results(
    payload: dict[str, Any],
    expected: str,
) -> None:
    result = real_agents._normalize_result(
        result=payload,
        output_fields=("result",),
    )

    assert result.status == "failed"

    assert result.error == expected


def test_result_helpers() -> None:
    assert (
        real_agents._result_list(
            {"warnings": "not-list"},
            "warnings",
        )
        == []
    )

    payload = {"other": 3}

    assert (
        real_agents._extract_output(
            payload,
            ("missing",),
        )
        is payload
    )

    assert real_agents._common_payload({"context": {}})["max_attempts"] == 2

    assert real_agents._common_payload({"context": {"agent_max_attempts": 5}})["max_attempts"] == 5


FAILURE_CASES: tuple[
    tuple[
        AgentNodeName,
        list[AgentNodeName],
    ],
    ...,
] = (
    (
        "resume_parser",
        [
            "resume_parser",
        ],
    ),
    (
        "job_description_analyzer",
        [
            "job_description_analyzer",
        ],
    ),
    (
        "resume_matching",
        [
            "resume_parser",
            "job_description_analyzer",
            "resume_matching",
        ],
    ),
    (
        "ats_optimization",
        [
            "resume_parser",
            "job_description_analyzer",
            "resume_matching",
            "ats_optimization",
        ],
    ),
    (
        "skill_gap",
        [
            "resume_parser",
            "job_description_analyzer",
            "resume_matching",
            "ats_optimization",
            "skill_gap",
        ],
    ),
    (
        "cover_letter",
        [
            "resume_parser",
            "job_description_analyzer",
            "resume_matching",
            "ats_optimization",
            "skill_gap",
            "cover_letter",
        ],
    ),
)


def build_failure_workflows(
    fail_node: AgentNodeName,
) -> real_agents.RealAgentWorkflows:
    async def maybe_fail(
        node: AgentNodeName,
    ) -> None:
        if node == fail_node:
            raise RuntimeError(f"{node} boom")

    async def resume_parser(
        *,
        text: str,
    ) -> dict[str, Any]:
        assert text

        await maybe_fail("resume_parser")

        return {"resume": {"skills": ["Python"]}}

    async def jd(
        *,
        text: str,
    ) -> dict[str, Any]:
        assert text

        await maybe_fail("job_description_analyzer")

        return {"job_description": {"job_title": ("Backend Engineer")}}

    async def matching(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
    ) -> dict[str, Any]:
        assert resume
        assert job_description
        assert resume_raw_text

        await maybe_fail("resume_matching")

        return {"match_result": {"score": 90}}

    async def ats(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        match_result: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
        max_bullet_rewrites: int = 5,
    ) -> dict[str, Any]:
        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert max_bullet_rewrites

        await maybe_fail("ats_optimization")

        return {"optimization": {"score": 92}}

    async def skill_gap(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        match_result: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
        max_roadmap_steps: int = 8,
        max_mini_projects: int = 3,
    ) -> dict[str, Any]:
        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert max_roadmap_steps
        assert max_mini_projects

        await maybe_fail("skill_gap")

        return {"skill_gap": {"gaps": []}}

    async def cover_letter(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        match_result: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
        candidate_name: str | None = None,
        company_context: str | None = None,
        tone: str = "professional",
        max_words: int = 300,
    ) -> dict[str, Any]:
        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert tone
        assert max_words

        del candidate_name
        del company_context

        await maybe_fail("cover_letter")

        return {"cover_letter": {"full_text": "Letter"}}

    return real_agents.RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=jd,
        resume_matching=matching,
        ats_optimization=ats,
        skill_gap=skill_gap,
        cover_letter=cover_letter,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "fail_node",
        "enabled_nodes",
    ),
    FAILURE_CASES,
)
async def test_each_real_executor_handles_failure(
    fail_node: AgentNodeName,
    enabled_nodes: list[AgentNodeName],
) -> None:
    result = await run_real_career_workflow(
        resume_raw_text=("Python backend developer"),
        job_description_text=("Backend Engineer"),
        workflows=(build_failure_workflows(fail_node)),
        enabled_nodes=enabled_nodes,
        max_retries=0,
    )

    assert result.status == "failed"

    assert result.failed_node == fail_node

    assert result.last_error is not None

    assert f"{fail_node} boom" in result.last_error


def test_registry_manager_validation() -> None:
    workflows = build_noop_workflows()

    with pytest.raises(
        ValueError,
        match="no workflow runner",
    ):
        real_agents.build_real_agent_registry(
            workflows,
            include_resume_version_manager=True,
            resume_version_agent=object(),
        )

    with_manager = build_noop_workflows(manager=noop_runner)

    with pytest.raises(
        ValueError,
        match="resume_version_agent",
    ):
        real_agents.build_real_agent_registry(
            with_manager,
            include_resume_version_manager=True,
        )

    registry = real_agents.build_real_agent_registry(
        with_manager,
        include_resume_version_manager=True,
        resume_version_agent=object(),
    )

    assert "resume_version_manager" in real_agents.registered_real_nodes(registry)


@pytest.mark.asyncio
async def test_version_manager_executor_failure() -> None:
    async def failing_version(
        *,
        agent: Any,
        request: dict[
            str,
            Any,
        ],
    ) -> dict[str, Any]:
        assert agent is not None
        assert request

        raise RuntimeError("version manager boom")

    workflows = build_noop_workflows(manager=failing_version)

    result = await run_real_career_workflow(
        resume_raw_text="Resume",
        job_description_text="JD",
        workflows=workflows,
        enabled_nodes=["resume_version_manager"],
        include_resume_version_manager=True,
        extra_context={
            "resume_version_agent": (object()),
            "resume_version_request": {"operation": "create"},
        },
        max_retries=0,
    )

    assert result.status == "failed"

    assert result.last_error is not None

    assert "version manager boom" in result.last_error
