"""LangChain Job Description Analyzer Agent."""

from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.prompts.job_description_analyzer import (
    JOB_DESCRIPTION_ANALYZER_SYSTEM_PROMPT,
    JOB_DESCRIPTION_ANALYZER_USER_PROMPT,
)
from app.schemas.job_description_parser import ParsedJobDescription

JobDescriptionAnalyzerRunnable = Runnable[
    dict[str, Any],
    ParsedJobDescription,
]


def build_job_description_analyzer_runnable(
    model: BaseChatModel,
) -> JobDescriptionAnalyzerRunnable:
    """Build the structured LangChain agent."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                JOB_DESCRIPTION_ANALYZER_SYSTEM_PROMPT,
            ),
            (
                "human",
                JOB_DESCRIPTION_ANALYZER_USER_PROMPT,
            ),
        ]
    )

    structured_model = model.with_structured_output(ParsedJobDescription)

    return cast(
        JobDescriptionAnalyzerRunnable,
        prompt | structured_model,
    )
