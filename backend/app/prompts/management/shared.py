"""Reusable guardrails shared between AI agents."""

from __future__ import annotations

EVIDENCE_GROUNDING_GUARDRAILS = """
Evidence grounding rules:

- Use only information supported by supplied source data.
- Never invent candidate skills, experience, projects,
  employers, achievements, certifications, or metrics.
- Clearly distinguish supported facts from suggestions.
- Reject unsupported factual claims.
""".strip()


STRUCTURED_OUTPUT_GUARDRAILS = """
Structured output rules:

- Follow the requested output schema exactly.
- Keep required fields present and internally consistent.
- Do not include additional prose outside the schema.
""".strip()


RETRY_GUARDRAILS = """
Retry rules:

- Correct every issue supplied in validation feedback.
- Do not repeat previously rejected unsupported claims.
- Preserve valid evidence from earlier attempts.
""".strip()


def compose_system_prompt(
    base_prompt: str,
    *guardrails: str,
) -> str:
    """Append reusable guardrails to a system prompt."""

    parts = [
        base_prompt.strip(),
        *[item.strip() for item in guardrails if item.strip()],
    ]

    return "\n\n".join(parts)
