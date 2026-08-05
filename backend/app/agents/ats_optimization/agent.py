"""LangChain ATS Optimization AI Agent."""

from __future__ import annotations

from typing import Any, cast

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.ats_optimization.state import (
    ATSOptimizationAnalysis,
)
from app.prompts.ats_optimization import (
    ATS_OPTIMIZATION_SYSTEM_PROMPT,
    ATS_OPTIMIZATION_USER_PROMPT,
)

ATSOptimizationRunnable = Runnable[
    dict[str, Any],
    ATSOptimizationAnalysis,
]


def build_ats_optimization_runnable(
    model: BaseChatModel,
) -> ATSOptimizationRunnable:
    """Build the structured ATS optimization agent."""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                ATS_OPTIMIZATION_SYSTEM_PROMPT,
            ),
            (
                "human",
                ATS_OPTIMIZATION_USER_PROMPT,
            ),
        ]
    )

    structured_model = model.with_structured_output(ATSOptimizationAnalysis)

    return cast(
        ATSOptimizationRunnable,
        prompt | structured_model,
    )
