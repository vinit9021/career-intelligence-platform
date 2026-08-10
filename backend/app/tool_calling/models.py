"""Models used by the tool-calling layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ToolCallStatus = Literal[
    "success",
    "denied",
    "invalid",
    "failed",
    "timeout",
]


class ToolCallRequest(BaseModel):
    """One structured agent tool request."""

    call_id: str = Field(default_factory=lambda: str(uuid4()))

    tool_name: str = Field(
        min_length=1,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResult(BaseModel):
    """Structured result returned to an agent."""

    call_id: str

    tool_name: str

    agent_name: str = Field(min_length=1)

    status: ToolCallStatus

    output: Any = None

    error: str | None = None

    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    duration_ms: float = Field(ge=0)

    metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        """Whether the tool executed successfully."""

        return self.status == "success"
