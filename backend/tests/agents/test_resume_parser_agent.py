"""Tests for Resume Parser Agent components."""

from app.agents.resume_parser.state import (
    ResumeParserAgentInput,
)
from app.prompts.resume_parser import (
    RESUME_PARSER_SYSTEM_PROMPT,
)


def test_agent_input_builds_prompt_payload() -> None:
    agent_input = ResumeParserAgentInput(
        resume_text="Python backend engineer",
        baseline_result={
            "skills": [
                "Python",
            ]
        },
        validation_feedback=["Email address was unsupported."],
    )

    payload = agent_input.to_prompt_payload()

    assert payload["resume_text"] == ("Python backend engineer")

    assert '"Python"' in payload["baseline_json"]

    assert "Email address was unsupported." in payload["validation_feedback"]


def test_resume_parser_prompt_forbids_fabrication() -> None:
    normalized_prompt = RESUME_PARSER_SYSTEM_PROMPT.casefold()

    assert "never invent" in normalized_prompt
    assert "explicitly supported" in normalized_prompt
    assert "source resume" in normalized_prompt
