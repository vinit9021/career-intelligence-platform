"""End-to-end Career Intelligence workflow executor."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.memory.manager import (
    MemoryManager,
)
from app.memory.store import (
    InMemoryMemoryStore,
)
from app.memory.workflow import (
    run_memory_aware_career_workflow,
)
from app.orchestration.real_agents import (
    RealAgentWorkflows,
)
from app.orchestration.state import (
    AgentNodeName,
    CareerWorkflowResult,
)
from app.prompts.management import (
    PromptManager,
    PromptNotFoundError,
    get_default_prompt_manager,
)
from app.tool_calling.runtime import (
    ToolRuntime,
    build_default_tool_runtime,
)
from app.workflow_execution.history import (
    InMemoryWorkflowHistory,
    WorkflowHistory,
)
from app.workflow_execution.models import (
    WorkflowExecutionRecord,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    WorkflowStepRecord,
    WorkflowStepStatus,
)


class WorkflowExecutionService:
    """Coordinates the complete agentic workflow."""

    def __init__(
        self,
        *,
        memory: MemoryManager,
        history: WorkflowHistory,
        prompt_manager: PromptManager,
        tool_runtime: ToolRuntime,
        workflows: RealAgentWorkflows | None = None,
        resume_version_agent: Any = None,
    ) -> None:
        self.memory = memory
        self.history = history
        self.prompt_manager = prompt_manager
        self.tool_runtime = tool_runtime
        self.workflows = workflows

        # Infrastructure dependencies remain outside
        # LangGraph checkpoint state.
        self.resume_version_agent = resume_version_agent

    def _prompt_metadata(
        self,
        nodes: list[AgentNodeName],
    ) -> dict[str, Any]:
        result: dict[
            str,
            Any,
        ] = {}

        for node in nodes:
            try:
                prompt = self.prompt_manager.resolve(node)

            except PromptNotFoundError:
                continue

            result[node] = {
                "version": (prompt.version),
                "checksum": (prompt.checksum),
            }

        return result

    def _tool_metadata(
        self,
        nodes: list[AgentNodeName],
    ) -> dict[str, list[str]]:
        return {node: (self.tool_runtime.tool_names_for_agent(node)) for node in nodes}

    def _execution_metadata(
        self,
        *,
        execution_id: str,
        nodes: list[AgentNodeName],
    ) -> dict[str, Any]:
        return {
            "execution_id": execution_id,
            "prompt_versions": (self._prompt_metadata(nodes)),
            "allowed_tools": (self._tool_metadata(nodes)),
            "memory_enabled": True,
            "tool_calling_enabled": True,
        }

    def _build_steps(
        self,
        *,
        request: WorkflowExecutionRequest,
        orchestration: CareerWorkflowResult | None,
        error: str | None = None,
    ) -> list[WorkflowStepRecord]:
        steps: list[WorkflowStepRecord] = []

        if orchestration is None:
            for node in request.enabled_nodes:
                steps.append(
                    WorkflowStepRecord(
                        node=node,
                        status="skipped",
                        error=error,
                    )
                )

            return steps

        executed = set(orchestration.execution_order)

        fallback_nodes = set(orchestration.fallback_nodes)

        for node in request.enabled_nodes:
            status: WorkflowStepStatus

            if node in executed:
                status = "completed"

            elif orchestration.failed_node == node:
                status = "failed"

            else:
                status = "skipped"

            node_error: str | None = None

            if status == "failed":
                node_error = orchestration.last_error

            steps.append(
                WorkflowStepRecord(
                    node=node,
                    status=status,
                    fallback_used=(node in fallback_nodes),
                    retry_count=(
                        orchestration.retry_counts.get(
                            node,
                            0,
                        )
                    ),
                    output_available=(node in orchestration.outputs),
                    error=node_error,
                )
            )

        return steps

    async def execute(
        self,
        request: WorkflowExecutionRequest,
    ) -> WorkflowExecutionResult:
        """Execute one end-to-end career workflow."""

        execution_id = str(uuid4())

        started_at = datetime.now(UTC)

        timer = perf_counter()

        metadata = self._execution_metadata(
            execution_id=execution_id,
            nodes=request.enabled_nodes,
        )

        initial_steps = [
            WorkflowStepRecord(
                node=node,
                status="pending",
            )
            for node in request.enabled_nodes
        ]

        await self.history.save(
            WorkflowExecutionRecord(
                execution_id=execution_id,
                user_id=request.user_id,
                session_id=(request.session_id),
                status="running",
                enabled_nodes=(request.enabled_nodes),
                steps=initial_steps,
                started_at=started_at,
            )
        )

        context = dict(request.extra_context)

        # Only serializable metadata is placed into
        # graph context.
        context["workflow_execution"] = metadata

        if request.include_resume_version_manager:
            if self.resume_version_agent is None:
                message = (
                    "Resume Version Manager "
                    "was enabled but "
                    "resume_version_agent "
                    "was not configured."
                )

                return await self._finish_failure(
                    request=request,
                    execution_id=(execution_id),
                    started_at=(started_at),
                    timer=timer,
                    metadata=metadata,
                    message=message,
                )

            context["resume_version_agent"] = self.resume_version_agent

        orchestration: CareerWorkflowResult | None = None

        try:
            orchestration = await run_memory_aware_career_workflow(
                memory=self.memory,
                user_id=request.user_id,
                session_id=(request.session_id),
                resume_raw_text=(request.resume_raw_text),
                job_description_text=(request.job_description_text),
                workflows=(self.workflows),
                enabled_nodes=(request.enabled_nodes),
                extra_context=context,
                max_retries=(request.max_retries),
                include_resume_version_manager=(request.include_resume_version_manager),
            )

        except Exception as exc:
            return await self._finish_failure(
                request=request,
                execution_id=(execution_id),
                started_at=started_at,
                timer=timer,
                metadata=metadata,
                message=str(exc),
            )

        finished_at = datetime.now(UTC)

        duration_ms = (perf_counter() - timer) * 1000

        steps = self._build_steps(
            request=request,
            orchestration=orchestration,
        )

        result = WorkflowExecutionResult(
            execution_id=execution_id,
            user_id=request.user_id,
            session_id=request.session_id,
            status=orchestration.status,
            outputs=orchestration.outputs,
            steps=steps,
            warnings=(orchestration.warnings),
            errors=(orchestration.errors),
            failed_node=(orchestration.failed_node),
            fallback_nodes=(orchestration.fallback_nodes),
            retry_counts=(orchestration.retry_counts),
            metadata=metadata,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
        )

        await self._save_terminal_record(
            result=result,
            enabled_nodes=(request.enabled_nodes),
        )

        return result

    async def _finish_failure(
        self,
        *,
        request: WorkflowExecutionRequest,
        execution_id: str,
        started_at: datetime,
        timer: float,
        metadata: dict[str, Any],
        message: str,
    ) -> WorkflowExecutionResult:
        finished_at = datetime.now(UTC)

        duration_ms = (perf_counter() - timer) * 1000

        result = WorkflowExecutionResult(
            execution_id=execution_id,
            user_id=request.user_id,
            session_id=request.session_id,
            status="failed",
            outputs={},
            steps=self._build_steps(
                request=request,
                orchestration=None,
                error=message,
            ),
            warnings=[],
            errors=[message],
            failed_node=None,
            fallback_nodes=[],
            retry_counts={},
            metadata=metadata,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
        )

        await self._save_terminal_record(
            result=result,
            enabled_nodes=(request.enabled_nodes),
        )

        return result

    async def _save_terminal_record(
        self,
        *,
        result: WorkflowExecutionResult,
        enabled_nodes: list[AgentNodeName],
    ) -> None:
        await self.history.save(
            WorkflowExecutionRecord(
                execution_id=(result.execution_id),
                user_id=result.user_id,
                session_id=(result.session_id),
                status=result.status,
                enabled_nodes=(enabled_nodes),
                steps=result.steps,
                output_keys=sorted(result.outputs),
                warnings=result.warnings,
                errors=result.errors,
                started_at=(result.started_at),
                finished_at=(result.finished_at),
                duration_ms=(result.duration_ms),
            )
        )


def build_default_workflow_execution_service(
    *,
    workflows: RealAgentWorkflows | None = None,
    resume_version_agent: Any = None,
) -> WorkflowExecutionService:
    """Build default development workflow executor."""

    memory = MemoryManager(InMemoryMemoryStore())

    history = InMemoryWorkflowHistory()

    return WorkflowExecutionService(
        memory=memory,
        history=history,
        prompt_manager=(get_default_prompt_manager()),
        tool_runtime=(build_default_tool_runtime()),
        workflows=workflows,
        resume_version_agent=(resume_version_agent),
    )
