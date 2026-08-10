"""Tests for existing agent prompt catalog."""

from app.prompts.management.catalog import (
    DEFAULT_PROMPT_MODULES,
    build_default_prompt_registry,
    load_prompt_definition,
)


def test_existing_prompt_modules_load() -> None:
    for spec in DEFAULT_PROMPT_MODULES:
        prompt = load_prompt_definition(spec)

        assert prompt.name == spec.name
        assert prompt.system_prompt
        assert prompt.user_prompt
        assert prompt.metadata["source_module"] == spec.module_name


def test_default_registry_contains_agents() -> None:
    registry = build_default_prompt_registry()

    assert set(registry.names()) == {
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
        "ats_optimization",
        "cover_letter",
        "skill_gap",
    }


def test_catalog_exposes_version_metadata() -> None:
    registry = build_default_prompt_registry()

    prompt = registry.get("ats_optimization")

    assert prompt.version == "1.0.0"
    assert prompt.agent_name
    assert len(prompt.checksum) == 64
