"""LangChain Skill Gap AI Agent."""

from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_core.runnables import Runnable

from app.agents.skill_gap.state import (
    SkillGapAnalysis,
)
from app.prompts.skill_gap import (
    SKILL_GAP_SYSTEM_PROMPT,
    SKILL_GAP_USER_PROMPT,
)

SkillGapRunnable = Runnable[
    dict[str, Any],
    SkillGapAnalysis,
]


def build_skill_gap_runnable(
    model: BaseChatModel,
) -> SkillGapRunnable:
    """Build structured Skill Gap Agent."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SKILL_GAP_SYSTEM_PROMPT,
            ),
            (
                "human",
                SKILL_GAP_USER_PROMPT,
            ),
        ]
    )

    structured_model = model.with_structured_output(SkillGapAnalysis)

    return cast(
        SkillGapRunnable,
        prompt | structured_model,
    )
