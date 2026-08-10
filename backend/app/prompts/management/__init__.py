"""Central prompt-management package."""

from app.prompts.management.catalog import (
    DEFAULT_PROMPT_MODULES,
    build_default_prompt_registry,
)
from app.prompts.management.manager import (
    PromptManager,
    build_chat_prompt,
    get_default_prompt_manager,
)
from app.prompts.management.models import (
    PromptDefinition,
    PromptModuleSpec,
)
from app.prompts.management.registry import (
    PromptAlreadyRegisteredError,
    PromptNotFoundError,
    PromptRegistry,
)

__all__ = [
    "DEFAULT_PROMPT_MODULES",
    "PromptAlreadyRegisteredError",
    "PromptDefinition",
    "PromptManager",
    "PromptModuleSpec",
    "PromptNotFoundError",
    "PromptRegistry",
    "build_chat_prompt",
    "build_default_prompt_registry",
    "get_default_prompt_manager",
]
