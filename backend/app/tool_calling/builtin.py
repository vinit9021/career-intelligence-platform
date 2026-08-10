"""Safe deterministic tools available to AI agents."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.tool_calling.registry import (
    ToolDefinition,
    ToolRegistry,
)


class EvidenceLookupInput(BaseModel):
    """Input for evidence lookup."""

    text: str = Field(min_length=1)

    query: str = Field(min_length=1)

    context_chars: int = Field(
        default=100,
        ge=0,
        le=500,
    )


class KeywordOverlapInput(BaseModel):
    """Input for keyword-overlap calculation."""

    resume_keywords: list[str] = Field(min_length=1)

    job_keywords: list[str] = Field(min_length=1)


async def _evidence_lookup(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    text = str(arguments["text"])

    query = str(arguments["query"])

    context_chars = int(arguments["context_chars"])

    normalized_text = text.casefold()
    normalized_query = query.casefold()

    index = normalized_text.find(normalized_query)

    if index < 0:
        return {
            "found": False,
            "query": query,
            "excerpt": None,
        }

    start = max(
        0,
        index - context_chars,
    )

    end = min(
        len(text),
        index + len(query) + context_chars,
    )

    return {
        "found": True,
        "query": query,
        "excerpt": text[start:end],
    }


def _normalize_keyword(
    value: str,
) -> str:
    return " ".join(value.casefold().split())


async def _keyword_overlap(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    resume_values = arguments["resume_keywords"]

    job_values = arguments["job_keywords"]

    if not isinstance(
        resume_values,
        list,
    ):
        raise TypeError("resume_keywords must be a list.")

    if not isinstance(
        job_values,
        list,
    ):
        raise TypeError("job_keywords must be a list.")

    resume = {_normalize_keyword(str(item)) for item in resume_values if str(item).strip()}

    job = {_normalize_keyword(str(item)) for item in job_values if str(item).strip()}

    matched = sorted(resume & job)

    missing = sorted(job - resume)

    score = (
        0.0
        if not job
        else round(
            len(matched) / len(job) * 100,
            2,
        )
    )

    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "match_percentage": score,
    }


def build_builtin_tool_registry() -> ToolRegistry:
    """Register built-in deterministic career tools."""

    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="evidence_lookup",
            description=("Search supplied text for exact evidence supporting a claim or keyword."),
            args_schema=(EvidenceLookupInput),
            handler=_evidence_lookup,
            timeout_seconds=5.0,
            metadata={
                "category": "validation",
                "source": "builtin",
            },
        )
    )

    registry.register(
        ToolDefinition(
            name="keyword_overlap",
            description=(
                "Compare resume keywords with job keywords and return matched and missing terms."
            ),
            args_schema=(KeywordOverlapInput),
            handler=_keyword_overlap,
            timeout_seconds=5.0,
            metadata={
                "category": "matching",
                "source": "builtin",
            },
        )
    )

    return registry
