"""Tests for the Job Description Analyzer Agent."""

from app.agents.job_description_analyzer.state import (
    JobDescriptionAnalyzerInput,
)
from app.agents.job_description_analyzer.validator import (
    validate_job_description_output,
)
from app.parsers import JobDescriptionParser
from app.prompts.job_description_analyzer import (
    JOB_DESCRIPTION_ANALYZER_SYSTEM_PROMPT,
)

JOB_DESCRIPTION_TEXT = """
Software Engineer

We Dolat Capital are looking for a Software Engineer
with 2+ years of experience.

Required skills:
- Python
- FastAPI
- PostgreSQL
- Git

Preferred skills:
- Docker
- AWS

Responsibilities:
- Develop backend APIs
- Write unit tests
- Review code
""".strip()


def test_agent_input_builds_prompt_payload() -> None:
    baseline = JobDescriptionParser().parse(JOB_DESCRIPTION_TEXT).model_dump(mode="python")

    agent_input = JobDescriptionAnalyzerInput(
        job_description_text=JOB_DESCRIPTION_TEXT,
        baseline_result=baseline,
        validation_feedback=["Company name was unsupported."],
    )

    payload = agent_input.to_prompt_payload()

    assert "Dolat Capital" in (payload["job_description_text"])
    assert "required_skills" in (payload["baseline_json"])
    assert "Company name was unsupported." in (payload["validation_feedback"])


def test_prompt_forbids_fabrication() -> None:
    prompt = JOB_DESCRIPTION_ANALYZER_SYSTEM_PROMPT.casefold()

    assert "never invent" in prompt
    assert "source job description" in prompt
    assert "required skills" in prompt


def test_validator_rejects_fake_company() -> None:
    parsed = JobDescriptionParser().parse(JOB_DESCRIPTION_TEXT)

    invalid_result = parsed.model_copy(
        update={
            "company_name": "Imaginary Labs",
        }
    )

    validation = validate_job_description_output(
        JOB_DESCRIPTION_TEXT,
        invalid_result,
    )

    assert validation.is_valid is False
    assert any("company name" in error.casefold() for error in validation.errors)
