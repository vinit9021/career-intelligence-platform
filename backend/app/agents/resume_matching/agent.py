"""LangChain Resume Matching AI Agent."""

from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.resume_matching.state import (
    SemanticResumeMatchingAnalysis,
)
from app.prompts.resume_matching import (
    RESUME_MATCHING_SYSTEM_PROMPT,
    RESUME_MATCHING_USER_PROMPT,
)

ResumeMatchingRunnable = Runnable[
    dict[str, Any],
    SemanticResumeMatchingAnalysis,
]


def build_resume_matching_runnable(
    model: BaseChatModel,
) -> ResumeMatchingRunnable:
    """Build the structured LangChain matching agent."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                RESUME_MATCHING_SYSTEM_PROMPT,
            ),
            (
                "human",
                RESUME_MATCHING_USER_PROMPT,
            ),
        ]
    )

    structured_model = model.with_structured_output(SemanticResumeMatchingAnalysis)

    return cast(
        ResumeMatchingRunnable,
        prompt | structured_model,
    )
