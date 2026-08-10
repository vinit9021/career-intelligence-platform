"""Application-level runtime for AI agent tools."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.tools import BaseTool

from app.tool_calling.audit import (
    ToolAuditSink,
)
from app.tool_calling.builtin import (
    build_builtin_tool_registry,
)
from app.tool_calling.executor import (
    ToolExecutor,
)
from app.tool_calling.langchain_adapter import (
    build_langchain_tools,
)
from app.tool_calling.models import (
    ToolCallRequest,
    ToolCallResult,
)
from app.tool_calling.permissions import (
    ToolPermissionPolicy,
)
from app.tool_calling.registry import (
    ToolRegistry,
)

DEFAULT_AGENT_TOOL_PERMISSIONS: dict[
    str,
    set[str],
] = {
    "resume_parser": {
        "evidence_lookup",
    },
    "job_description_analyzer": {
        "evidence_lookup",
    },
    "resume_matching": {
        "evidence_lookup",
        "keyword_overlap",
    },
    "ats_optimization": {
        "evidence_lookup",
        "keyword_overlap",
    },
    "skill_gap": {
        "evidence_lookup",
        "keyword_overlap",
    },
    "cover_letter": {
        "evidence_lookup",
    },
}


@dataclass(frozen=True)
class ToolRuntime:
    """Dependencies used by tool-enabled agents."""

    registry: ToolRegistry

    executor: ToolExecutor

    permissions: ToolPermissionPolicy

    async def call(
        self,
        *,
        agent_name: str,
        request: ToolCallRequest,
    ) -> ToolCallResult:
        """Execute a tool for one agent."""

        return await self.executor.execute(
            agent_name=agent_name,
            request=request,
        )

    def tools_for_agent(
        self,
        agent_name: str,
    ) -> list[BaseTool]:
        """Return LangChain-compatible allowed tools."""

        return build_langchain_tools(
            registry=self.registry,
            executor=self.executor,
            agent_name=agent_name,
        )

    def tool_names_for_agent(
        self,
        agent_name: str,
    ) -> list[str]:
        """Return allowed registered tool names."""

        return sorted(
            name
            for name in self.registry.names()
            if self.permissions.is_allowed(
                agent_name=agent_name,
                tool_name=name,
            )
        )


def build_default_tool_runtime(
    *,
    audit_sink: ToolAuditSink | None = None,
) -> ToolRuntime:
    """Build production default tool runtime."""

    registry = build_builtin_tool_registry()

    permissions = ToolPermissionPolicy(DEFAULT_AGENT_TOOL_PERMISSIONS)

    executor = ToolExecutor(
        registry=registry,
        permissions=permissions,
        audit_sink=audit_sink,
    )

    return ToolRuntime(
        registry=registry,
        executor=executor,
        permissions=permissions,
    )
