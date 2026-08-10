"""Catalog of prompts from existing AI agents."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

from app.prompts.management.models import (
    PromptDefinition,
    PromptModuleSpec,
)
from app.prompts.management.registry import (
    PromptRegistry,
)

DEFAULT_PROMPT_MODULES: tuple[
    PromptModuleSpec,
    ...,
] = (
    PromptModuleSpec(
        name="resume_parser",
        agent_name="Resume Parser Agent",
        module_name=("app.prompts.resume_parser"),
        version="1.0.0",
        description=("Structured resume parsing prompt."),
    ),
    PromptModuleSpec(
        name="job_description_analyzer",
        agent_name=("Job Description Analyzer Agent"),
        module_name=("app.prompts.job_description_analyzer"),
        version="1.0.0",
        description=("Job description analysis prompt."),
    ),
    PromptModuleSpec(
        name="resume_matching",
        agent_name="Resume Matching Agent",
        module_name=("app.prompts.resume_matching"),
        version="1.0.0",
        description=("Semantic resume-job matching prompt."),
    ),
    PromptModuleSpec(
        name="ats_optimization",
        agent_name="ATS Optimization Agent",
        module_name=("app.prompts.ats_optimization"),
        version="1.0.0",
        description=("ATS resume optimization prompt."),
    ),
    PromptModuleSpec(
        name="cover_letter",
        agent_name="Cover Letter Agent",
        module_name=("app.prompts.cover_letter"),
        version="1.0.0",
        description=("Evidence-grounded cover letter prompt."),
    ),
    PromptModuleSpec(
        name="skill_gap",
        agent_name="Skill Gap Agent",
        module_name=("app.prompts.skill_gap"),
        version="1.0.0",
        description=("Skill-gap and learning roadmap prompt."),
    ),
)


def _find_prompt_constant(
    module: ModuleType,
    suffix: str,
) -> str:
    """Discover one prompt constant by suffix."""

    matches: list[str] = []

    for name in dir(module):
        if not name.endswith(suffix):
            continue

        value = getattr(
            module,
            name,
        )

        if isinstance(value, str):
            matches.append(value)

    if not matches:
        raise ValueError(f"No prompt constant ending with {suffix} found in {module.__name__}.")

    if len(matches) > 1:
        raise ValueError(
            f"Multiple prompt constants ending with {suffix} found in {module.__name__}."
        )

    return matches[0]


def load_prompt_definition(
    spec: PromptModuleSpec,
) -> PromptDefinition:
    """Load one existing prompt module."""

    module = import_module(spec.module_name)

    system_prompt = _find_prompt_constant(
        module,
        "SYSTEM_PROMPT",
    )

    user_prompt = _find_prompt_constant(
        module,
        "USER_PROMPT",
    )

    return PromptDefinition(
        name=spec.name,
        agent_name=spec.agent_name,
        version=spec.version,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        description=spec.description,
        tags=[
            "agentic-ai",
            "groq",
            "langchain",
        ],
        metadata={
            "source_module": (spec.module_name),
        },
    )


def build_default_prompt_registry() -> PromptRegistry:
    """Build registry for implemented AI agents."""

    registry = PromptRegistry()

    for spec in DEFAULT_PROMPT_MODULES:
        registry.register(load_prompt_definition(spec))

    return registry
