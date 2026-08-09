"""Deterministic fallback cover-letter generator."""

from __future__ import annotations

from app.agents.cover_letter.state import (
    CoverLetterRequest,
    CoverLetterResult,
)


def _deduplicate(
    values: list[str],
) -> list[str]:
    return list(dict.fromkeys(values))


def build_cover_letter_fallback(
    request: CoverLetterRequest,
) -> CoverLetterResult:
    """Generate a safe deterministic fallback."""

    job = request.job_description
    match = request.match_result

    role = job.job_title or "the advertised role"

    company = job.company_name or "your organization"

    matched_skills = _deduplicate(
        [
            *match.matched_required_skills,
            *match.matched_preferred_skills,
            *match.matched_technologies,
        ]
    )

    top_skills = matched_skills[:4]

    greeting = "Dear Hiring Team,"

    opening = f"I am writing to express my interest in the {role} opportunity at {company}."

    resume_data = request.resume.model_dump(mode="python")

    summary = str(resume_data.get("summary") or "").strip()

    body_paragraphs: list[str] = []

    if summary:
        body_paragraphs.append(summary)

    if top_skills:
        body_paragraphs.append(
            "My background includes relevant "
            "experience with " + ", ".join(top_skills) + ", which aligns with key requirements "
            "for this position."
        )

    if not body_paragraphs:
        body_paragraphs.append(
            "My background contains experience relevant "
            "to the requirements identified in the "
            "resume and job-description comparison."
        )

    closing = (
        "I would welcome the opportunity to discuss how "
        "my background could contribute to your team."
    )

    sign_off = (
        "Sincerely,"
        if request.candidate_name is None
        else ("Sincerely,\n" + request.candidate_name)
    )

    full_text = "\n\n".join(
        [
            greeting,
            opening,
            *body_paragraphs,
            closing,
            sign_off,
        ]
    )

    return CoverLetterResult(
        target_role=job.job_title,
        company_name=job.company_name,
        greeting=greeting,
        opening_paragraph=opening,
        body_paragraphs=body_paragraphs,
        closing_paragraph=closing,
        sign_off=sign_off,
        full_text=full_text,
        skills_mentioned=top_skills,
        evidence=[],
        warnings=[
            "AI cover-letter generation was unavailable "
            "or invalid. A deterministic cover letter "
            "was returned."
        ],
        deterministic_fallback=True,
    )
