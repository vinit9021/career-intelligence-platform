"""LangChain implementation of the Resume Parser AI Agent."""

from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.prompts.resume_parser import (
    RESUME_PARSER_SYSTEM_PROMPT,
    RESUME_PARSER_USER_PROMPT,
)
from app.schemas.resume_parsing import ResumeStructuredContent

ResumeParserRunnable = Runnable[
    dict[str, Any],
    ResumeStructuredContent,
]


def build_resume_parser_runnable(
    model: BaseChatModel,
) -> ResumeParserRunnable:
    """Create the structured LangChain resume-parsing runnable."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                RESUME_PARSER_SYSTEM_PROMPT,
            ),
            (
                "human",
                RESUME_PARSER_USER_PROMPT,
            ),
        ]
    )

    structured_model = model.with_structured_output(ResumeStructuredContent)

    return cast(
        ResumeParserRunnable,
        prompt | structured_model,
    )
