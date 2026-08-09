"""LangChain Cover Letter AI Agent."""

from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_core.runnables import Runnable

from app.agents.cover_letter.state import (
    CoverLetterAnalysis,
)
from app.prompts.cover_letter import (
    COVER_LETTER_SYSTEM_PROMPT,
    COVER_LETTER_USER_PROMPT,
)

CoverLetterRunnable = Runnable[
    dict[str, Any],
    CoverLetterAnalysis,
]


def build_cover_letter_runnable(
    model: BaseChatModel,
) -> CoverLetterRunnable:
    """Build structured LangChain cover-letter agent."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                COVER_LETTER_SYSTEM_PROMPT,
            ),
            (
                "human",
                COVER_LETTER_USER_PROMPT,
            ),
        ]
    )

    structured_model = model.with_structured_output(CoverLetterAnalysis)

    return cast(
        CoverLetterRunnable,
        prompt | structured_model,
    )
