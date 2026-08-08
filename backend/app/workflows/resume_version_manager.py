"""LangGraph workflow for Resume Version Manager."""

from __future__ import annotations

from typing import Any, Literal, TypedDict, cast
from uuid import UUID, uuid4

from langchain_core.runnables import (
    RunnableLambda,
)
from langgraph.checkpoint.memory import (
    InMemorySaver,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from pydantic import BaseModel, Field

from app.agents.resume_version_manager.agent import (
    ResumeVersionManagerAgent,
)
from app.schemas.resume_version import (
    ResumeSubmissionCreate,
    ResumeSubmissionRead,
    ResumeVersionCreate,
    ResumeVersionRead,
)

ResumeVersionOperation = Literal[
    "create",
    "activate",
    "submit",
]


class ResumeVersionManagerRequest(BaseModel):
    """Command supplied to the workflow."""

    operation: ResumeVersionOperation

    create_request: ResumeVersionCreate | None = None

    user_id: UUID | None = None
    version_id: UUID | None = None

    submission_request: ResumeSubmissionCreate | None = None


class ResumeVersionManagerResponse(BaseModel):
    """Workflow response."""

    status: Literal[
        "completed",
        "failed",
    ]

    version: ResumeVersionRead | None = None

    submission: ResumeSubmissionRead | None = None

    errors: list[str] = Field(default_factory=list)


class ResumeVersionManagerState(
    TypedDict,
    total=False,
):
    request: ResumeVersionManagerRequest
    response: ResumeVersionManagerResponse


def _validate_request(
    request: ResumeVersionManagerRequest,
) -> None:
    if request.operation == "create" and request.create_request is None:
        raise ValueError("create_request is required.")

    if request.operation == "activate":
        if request.user_id is None or request.version_id is None:
            raise ValueError("user_id and version_id are required.")

    if request.operation == "submit" and request.submission_request is None:
        raise ValueError("submission_request is required.")


def build_resume_version_manager_workflow(
    agent: ResumeVersionManagerAgent,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build deterministic LangGraph workflow."""

    async def execute(
        state: ResumeVersionManagerState,
    ) -> dict[str, Any]:
        request = state["request"]

        try:
            _validate_request(request)

            if request.operation == "create":
                create_request = request.create_request

                if create_request is None:
                    raise ValueError("create_request is required.")

                version = await agent.create_variant(create_request)

                response = ResumeVersionManagerResponse(
                    status="completed",
                    version=version,
                )

            elif request.operation == "activate":
                if request.user_id is None or request.version_id is None:
                    raise ValueError("Activation identifiers are required.")

                version = await agent.set_active(
                    user_id=request.user_id,
                    version_id=request.version_id,
                )

                response = ResumeVersionManagerResponse(
                    status="completed",
                    version=version,
                )

            else:
                submission_request = request.submission_request

                if submission_request is None:
                    raise ValueError("submission_request is required.")

                submission = await agent.track_submission(submission_request)

                response = ResumeVersionManagerResponse(
                    status="completed",
                    submission=submission,
                )

        except Exception as exc:
            response = ResumeVersionManagerResponse(
                status="failed",
                errors=[str(exc)],
            )

        return {"response": response}

    builder = StateGraph(ResumeVersionManagerState)

    builder.add_node(
        "execute",
        cast(
            Any,
            RunnableLambda(execute),
        ),
    )

    builder.add_edge(
        START,
        "execute",
    )

    builder.add_edge(
        "execute",
        END,
    )

    if use_checkpointer:
        return builder.compile(checkpointer=InMemorySaver())

    return builder.compile()


async def run_resume_version_manager_workflow(
    *,
    agent: ResumeVersionManagerAgent,
    request: ResumeVersionManagerRequest,
    thread_id: str | None = None,
) -> ResumeVersionManagerResponse:
    """Execute Resume Version Manager."""

    graph = build_resume_version_manager_workflow(agent)

    raw_result = await graph.ainvoke(
        {
            "request": request,
        },
        config={"configurable": {"thread_id": (thread_id or str(uuid4()))}},
    )

    response = raw_result.get("response")

    if not isinstance(
        response,
        ResumeVersionManagerResponse,
    ):
        return ResumeVersionManagerResponse(
            status="failed",
            errors=["Resume Version Manager returned invalid state."],
        )

    return response
