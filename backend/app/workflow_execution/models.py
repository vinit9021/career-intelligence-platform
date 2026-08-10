"""Models for end-to-end workflow execution."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from app.orchestration.state import (
    CORE_PIPELINE_ORDER,
    AgentNodeName,
)

WorkflowExecutionStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
]

WorkflowStepStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
]


class WorkflowExecutionRequest(BaseModel):
    """Input for one Career Intelligence workflow."""

    user_id: str = Field(min_length=1)

    session_id: str = Field(min_length=1)

    resume_raw_text: str = Field(min_length=1)

    job_description_text: str = Field(min_length=1)

    enabled_nodes: list[AgentNodeName] = Field(default_factory=lambda: list(CORE_PIPELINE_ORDER))

    extra_context: dict[
        str,
        Any,
    ] = Field(default_factory=dict)

    max_retries: int = Field(
        default=1,
        ge=0,
        le=5,
    )

    include_resume_version_manager: bool = False

    @field_validator(
        "user_id",
        "session_id",
        "resume_raw_text",
        "job_description_text",
    )
    @classmethod
    def reject_blank_values(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Value cannot be blank.")

        return cleaned

    @field_validator("enabled_nodes")
    @classmethod
    def validate_enabled_nodes(
        cls,
        value: list[AgentNodeName],
    ) -> list[AgentNodeName]:
        if not value:
            raise ValueError("At least one workflow node must be enabled.")

        if len(value) != len(set(value)):
            raise ValueError("enabled_nodes cannot contain duplicates.")

        return value


class WorkflowStepRecord(BaseModel):
    """Final execution state of one agent step."""

    node: AgentNodeName

    status: WorkflowStepStatus

    fallback_used: bool = False

    retry_count: int = Field(
        default=0,
        ge=0,
    )

    output_available: bool = False

    error: str | None = None


class WorkflowExecutionRecord(BaseModel):
    """Compact workflow record stored in history."""

    execution_id: str = Field(default_factory=lambda: str(uuid4()))

    user_id: str

    session_id: str

    status: WorkflowExecutionStatus

    enabled_nodes: list[AgentNodeName]

    steps: list[WorkflowStepRecord] = Field(default_factory=list)

    output_keys: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)

    errors: list[str] = Field(default_factory=list)

    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    finished_at: datetime | None = None

    duration_ms: float | None = Field(
        default=None,
        ge=0,
    )


class WorkflowExecutionResult(BaseModel):
    """Structured final workflow result."""

    execution_id: str

    user_id: str

    session_id: str

    status: WorkflowExecutionStatus

    outputs: dict[str, Any] = Field(default_factory=dict)

    steps: list[WorkflowStepRecord] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)

    errors: list[str] = Field(default_factory=list)

    failed_node: AgentNodeName | None = None

    fallback_nodes: list[str] = Field(default_factory=list)

    retry_counts: dict[
        str,
        int,
    ] = Field(default_factory=dict)

    metadata: dict[
        str,
        Any,
    ] = Field(default_factory=dict)

    started_at: datetime

    finished_at: datetime

    duration_ms: float = Field(ge=0)
