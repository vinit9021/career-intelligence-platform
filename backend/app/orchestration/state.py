"""Shared state for central LangGraph orchestration."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

AgentNodeName = Literal[
    "resume_parser",
    "job_description_analyzer",
    "resume_matching",
    "ats_optimization",
    "skill_gap",
    "cover_letter",
    "resume_version_manager",
]

WorkflowStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
]

AgentExecutionStatus = Literal[
    "completed",
    "failed",
]

GraphRoute = (
    AgentNodeName
    | Literal[
        "fallback",
        "finalize",
    ]
)


CORE_PIPELINE_ORDER: tuple[
    AgentNodeName,
    ...,
] = (
    "resume_parser",
    "job_description_analyzer",
    "resume_matching",
    "ats_optimization",
    "skill_gap",
    "cover_letter",
)

PIPELINE_ORDER: tuple[
    AgentNodeName,
    ...,
] = (
    *CORE_PIPELINE_ORDER,
    "resume_version_manager",
)


class AgentNodeResult(BaseModel):
    """Standard result returned by an agent adapter."""

    status: AgentExecutionStatus

    output: Any = None

    warnings: list[str] = Field(default_factory=list)

    error: str | None = None

    retryable: bool = True


class CareerWorkflowRequest(BaseModel):
    """Public input for the central workflow."""

    enabled_nodes: list[AgentNodeName] = Field(default_factory=lambda: list(CORE_PIPELINE_ORDER))

    initial_context: dict[str, Any] = Field(default_factory=dict)


class CareerWorkflowState(
    TypedDict,
    total=False,
):
    """Checkpoint-safe LangGraph state."""

    # Important:
    # Stored as dictionary rather than BaseModel because
    # LangGraph checkpoints serialize workflow state.
    request: dict[str, Any]

    context: dict[str, Any]

    outputs: dict[str, Any]

    execution_order: list[str]

    fallback_nodes: list[str]

    retry_counts: dict[str, int]

    max_retries: int

    current_node: AgentNodeName | None

    failed_node: AgentNodeName | None

    next_node: GraphRoute | None

    status: WorkflowStatus

    warnings: list[str]

    errors: list[str]

    last_error: str | None


class CareerWorkflowResult(BaseModel):
    """Final orchestration result."""

    status: WorkflowStatus

    outputs: dict[str, Any] = Field(default_factory=dict)

    execution_order: list[str] = Field(default_factory=list)

    fallback_nodes: list[str] = Field(default_factory=list)

    retry_counts: dict[str, int] = Field(default_factory=dict)

    warnings: list[str] = Field(default_factory=list)

    errors: list[str] = Field(default_factory=list)

    failed_node: AgentNodeName | None = None

    last_error: str | None = None
