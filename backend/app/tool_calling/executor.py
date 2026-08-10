"""Safe execution engine for agent tool calls."""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any

from pydantic import ValidationError

from app.tool_calling.audit import (
    NullToolAuditSink,
    ToolAuditSink,
)
from app.tool_calling.models import (
    ToolCallRequest,
    ToolCallResult,
    ToolCallStatus,
)
from app.tool_calling.permissions import (
    ToolPermissionPolicy,
)
from app.tool_calling.registry import (
    ToolNotFoundError,
    ToolRegistry,
)
from app.tool_calling.serialization import (
    to_tool_value,
)


class ToolExecutor:
    """Validates, authorizes and executes agent tools."""

    def __init__(
        self,
        *,
        registry: ToolRegistry,
        permissions: ToolPermissionPolicy,
        audit_sink: ToolAuditSink | None = None,
    ) -> None:
        self.registry = registry
        self.permissions = permissions

        self.audit_sink = audit_sink if audit_sink is not None else NullToolAuditSink()

    async def execute(
        self,
        *,
        agent_name: str,
        request: ToolCallRequest,
    ) -> ToolCallResult:
        """Execute one structured tool request."""

        started = perf_counter()

        try:
            definition = self.registry.get(request.tool_name)

        except ToolNotFoundError:
            return await self._finish(
                agent_name=agent_name,
                request=request,
                status="invalid",
                started=started,
                error=(f"Unknown tool: {request.tool_name}"),
            )

        if not self.permissions.is_allowed(
            agent_name=agent_name,
            tool_name=request.tool_name,
        ):
            return await self._finish(
                agent_name=agent_name,
                request=request,
                status="denied",
                started=started,
                error=("Agent is not permitted to use this tool."),
            )

        try:
            validated = definition.args_schema.model_validate(request.arguments)

        except ValidationError as exc:
            return await self._finish(
                agent_name=agent_name,
                request=request,
                status="invalid",
                started=started,
                error=(f"Invalid tool arguments: {exc}"),
            )

        arguments = validated.model_dump(mode="python")

        try:
            raw_output = await asyncio.wait_for(
                definition.handler(arguments),
                timeout=(definition.timeout_seconds),
            )

            output = to_tool_value(raw_output)

        except TimeoutError:
            return await self._finish(
                agent_name=agent_name,
                request=request,
                status="timeout",
                started=started,
                error=(f"Tool execution exceeded {definition.timeout_seconds} seconds."),
                metadata=definition.metadata,
            )

        except Exception as exc:
            return await self._finish(
                agent_name=agent_name,
                request=request,
                status="failed",
                started=started,
                error=str(exc),
                metadata=definition.metadata,
            )

        return await self._finish(
            agent_name=agent_name,
            request=request,
            status="success",
            started=started,
            output=output,
            metadata=definition.metadata,
        )

    async def _finish(
        self,
        *,
        agent_name: str,
        request: ToolCallRequest,
        status: ToolCallStatus,
        started: float,
        output: Any = None,
        error: str | None = None,
        metadata: (dict[str, str] | None) = None,
    ) -> ToolCallResult:
        duration_ms = (perf_counter() - started) * 1000

        result = ToolCallResult(
            call_id=request.call_id,
            tool_name=request.tool_name,
            agent_name=agent_name,
            status=status,
            output=output,
            error=error,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        await self.audit_sink.write(result)

        return result
