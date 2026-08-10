"""Adapters exposing registered tools to LangChain agents."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import (
    BaseTool,
    StructuredTool,
)

from app.tool_calling.executor import (
    ToolExecutor,
)
from app.tool_calling.models import (
    ToolCallRequest,
)
from app.tool_calling.registry import (
    ToolDefinition,
    ToolRegistry,
)


def _build_langchain_tool(
    *,
    definition: ToolDefinition,
    executor: ToolExecutor,
    agent_name: str,
) -> BaseTool:
    async def invoke(
        **kwargs: Any,
    ) -> dict[str, Any]:
        result = await executor.execute(
            agent_name=agent_name,
            request=ToolCallRequest(
                tool_name=definition.name,
                arguments=kwargs,
            ),
        )

        return result.model_dump(mode="json")

    return StructuredTool.from_function(
        coroutine=invoke,
        name=definition.name,
        description=definition.description,
        args_schema=definition.args_schema,
        infer_schema=False,
    )


def build_langchain_tools(
    *,
    registry: ToolRegistry,
    executor: ToolExecutor,
    agent_name: str,
) -> list[BaseTool]:
    """Build only the tools permitted for an agent."""

    result: list[BaseTool] = []

    for definition in registry.definitions():
        if not (
            executor.permissions.is_allowed(
                agent_name=agent_name,
                tool_name=definition.name,
            )
        ):
            continue

        result.append(
            _build_langchain_tool(
                definition=definition,
                executor=executor,
                agent_name=agent_name,
            )
        )

    return result
