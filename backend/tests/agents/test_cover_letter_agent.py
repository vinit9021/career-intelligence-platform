"""Tests for Cover Letter AI Agent."""

from app.agents.cover_letter.state import (
    CoverLetterAnalysis,
    CoverLetterEvidence,
    CoverLetterRequest,
)
from app.agents.cover_letter.validator import (
    validate_cover_letter_output,
)
from app.matching import match_resume_to_job
from app.prompts.cover_letter import (
    COVER_LETTER_SYSTEM_PROMPT,
)
from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    ParsedJobDescription,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)


def build_request() -> CoverLetterRequest:
    resume = ResumeStructuredContent.model_validate(
        {
            "summary": ("Backend engineer with Python, FastAPI, and AWS experience."),
            "skills": [
                "Python",
                "FastAPI",
                "AWS",
            ],
            "experience": [
                ("Built backend APIs using Python and FastAPI."),
                ("Deployed backend services on AWS for production workloads."),
            ],
            "education": [],
            "projects": [("Built an analytics platform using FastAPI.")],
            "certifications": [],
        }
    )

    job = ParsedJobDescription(
        job_title="Backend Engineer",
        company_name="Example Labs",
        required_skills=[
            "Python",
            "FastAPI",
            "Kubernetes",
        ],
        preferred_skills=[
            "AWS",
        ],
        technologies=[
            "Python",
            "FastAPI",
            "AWS",
        ],
        responsibilities=[
            "Build scalable backend APIs",
        ],
        qualifications=[],
        experience=JobExperienceRequirement(),
        education_requirements=[],
        seniority_level="unspecified",
        ats_keywords=[
            "Python",
            "FastAPI",
            "AWS",
            "Kubernetes",
        ],
        normalized_text=(
            "Example Labs seeks a Backend Engineer with Python, FastAPI, AWS and Kubernetes."
        ),
        metadata=JobDescriptionParserMetadata(
            parser_name="test",
            parser_version="1.0.0",
            character_count=100,
        ),
    )

    raw_text = (
        "Backend engineer with Python, FastAPI, and "
        "AWS experience. Built backend APIs using "
        "Python and FastAPI. Deployed backend services "
        "on AWS for production workloads."
    )

    match_result = match_resume_to_job(
        resume=resume,
        job_description=job,
        resume_raw_text=raw_text,
    )

    return CoverLetterRequest(
        resume=resume,
        job_description=job,
        match_result=match_result,
        resume_raw_text=raw_text,
        candidate_name="Alex Candidate",
        tone="professional",
        max_words=300,
    )


def valid_analysis() -> CoverLetterAnalysis:
    return CoverLetterAnalysis(
        greeting="Dear Hiring Team,",
        opening_paragraph=("I am excited to apply for the Backend Engineer role at Example Labs."),
        body_paragraphs=[
            (
                "My backend experience includes "
                "Python and FastAPI, including work "
                "building backend APIs."
            ),
            ("I have also deployed backend services on AWS for production workloads."),
        ],
        closing_paragraph=(
            "I would welcome the opportunity to "
            "contribute my backend engineering "
            "experience to Example Labs."
        ),
        sign_off=("Sincerely,\nAlex Candidate"),
        skills_mentioned=[
            "Python",
            "FastAPI",
            "AWS",
        ],
        evidence=[
            CoverLetterEvidence(
                claim=("work building backend APIs"),
                resume_excerpt=("Built backend APIs using Python and FastAPI."),
                source_section="experience",
            ),
            CoverLetterEvidence(
                claim=("deployed backend services on AWS"),
                resume_excerpt=("Deployed backend services on AWS for production workloads."),
                source_section="experience",
            ),
        ],
        warnings=[],
        rationale=("The letter emphasizes resume-supported requirements relevant to the role."),
    )


def test_prompt_contains_guardrails() -> None:
    prompt = COVER_LETTER_SYSTEM_PROMPT.casefold()

    assert "never invent" in prompt
    assert "exact resume excerpts" in prompt
    assert "maximum word count" in prompt


def test_validator_accepts_grounded_letter() -> None:
    result = validate_cover_letter_output(
        build_request(),
        valid_analysis(),
    )

    assert result.is_valid is True
    assert result.errors == []


def test_validator_rejects_unsupported_skill() -> None:
    analysis = valid_analysis()

    invalid = analysis.model_copy(
        update={
            "body_paragraphs": [
                *analysis.body_paragraphs,
                ("I have extensive Kubernetes production experience."),
            ],
            "skills_mentioned": [
                *analysis.skills_mentioned,
                "Kubernetes",
            ],
        }
    )

    result = validate_cover_letter_output(
        build_request(),
        invalid,
    )

    assert result.is_valid is False

    assert any(
        "not supported by the resume" in error or "unsupported job keyword" in error
        for error in result.errors
    )


def test_validator_rejects_fabricated_metric() -> None:
    analysis = valid_analysis()

    invalid = analysis.model_copy(
        update={"body_paragraphs": [("Improved backend performance by 40% using Python.")]}
    )

    result = validate_cover_letter_output(
        build_request(),
        invalid,
    )

    assert result.is_valid is False

    assert any("unsupported numeric" in error for error in result.errors)
