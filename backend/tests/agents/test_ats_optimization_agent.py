"""Tests for the ATS Optimization AI Agent."""

from app.agents.ats_optimization.state import (
    ATSBulletRewrite,
    ATSKeywordRecommendation,
    ATSOptimizationAgentInput,
    ATSOptimizationAnalysis,
    ATSOptimizationRequest,
    ATSSectionRecommendation,
    ATSSummaryRewrite,
)
from app.agents.ats_optimization.validator import (
    validate_ats_optimization_output,
)
from app.ats.optimizer import build_ats_baseline
from app.matching import match_resume_to_job
from app.prompts.ats_optimization import (
    ATS_OPTIMIZATION_SYSTEM_PROMPT,
)
from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    ParsedJobDescription,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)


def build_request() -> ATSOptimizationRequest:
    resume = ResumeStructuredContent.model_validate(
        {
            "summary": ("Backend engineer with Python and AWS experience."),
            "skills": [
                "Python",
                "AWS",
                "FastAPI",
            ],
            "experience": [("Deployed backend services on AWS for production workloads.")],
            "education": [],
            "projects": [("Built FastAPI services for an analytics platform.")],
            "certifications": [],
        }
    )

    job = ParsedJobDescription(
        job_title="Backend Engineer",
        company_name="Example Labs",
        required_skills=[
            "Python",
            "Kubernetes",
        ],
        preferred_skills=[
            "FastAPI",
        ],
        technologies=[
            "AWS",
        ],
        responsibilities=[("Deploy backend services to cloud infrastructure")],
        qualifications=[],
        experience=JobExperienceRequirement(),
        education_requirements=[],
        seniority_level="unspecified",
        ats_keywords=[
            "Python",
            "AWS",
            "Kubernetes",
            "FastAPI",
        ],
        normalized_text=("Backend Engineer requiring Python, AWS, FastAPI and Kubernetes."),
        metadata=JobDescriptionParserMetadata(
            parser_name="test",
            parser_version="1.0.0",
            character_count=100,
        ),
    )

    raw_text = (
        "Backend engineer with Python and AWS experience. "
        "Deployed backend services on AWS for production "
        "workloads. Built FastAPI services for an "
        "analytics platform."
    )

    match_result = match_resume_to_job(
        resume=resume,
        job_description=job,
        resume_raw_text=raw_text,
    )

    return ATSOptimizationRequest(
        resume=resume,
        job_description=job,
        match_result=match_result,
        resume_raw_text=raw_text,
        max_bullet_rewrites=3,
    )


def valid_analysis() -> ATSOptimizationAnalysis:
    return ATSOptimizationAnalysis(
        proposed_ats_score=88,
        keyword_recommendations=[
            ATSKeywordRecommendation(
                keyword="AWS",
                priority="high",
                target_section="summary",
                recommendation=("Retain AWS in the professional summary."),
                currently_supported_by_resume=True,
                safe_to_add=True,
                resume_evidence=("Deployed backend services on AWS for production workloads."),
            ),
            ATSKeywordRecommendation(
                keyword="Kubernetes",
                priority="high",
                target_section="skills",
                recommendation=("Add Kubernetes only when the candidate has factual experience."),
                currently_supported_by_resume=False,
                safe_to_add=False,
                resume_evidence=None,
            ),
        ],
        summary_rewrite=ATSSummaryRewrite(
            original_summary=("Backend engineer with Python and AWS experience."),
            rewritten_summary=("Backend engineer with Python, AWS, and FastAPI experience."),
            keywords_added=[
                "FastAPI",
            ],
            evidence_excerpts=[("Built FastAPI services for an analytics platform.")],
            rationale=("Places an existing relevant technology in the summary."),
        ),
        bullet_rewrites=[
            ATSBulletRewrite(
                source_section="experience",
                original_text=("Deployed backend services on AWS for production workloads."),
                rewritten_text=("Deployed production backend services on AWS."),
                keywords_added=[
                    "AWS",
                ],
                rationale=("Moves the job-relevant technology closer to the action."),
            )
        ],
        section_recommendations=[
            ATSSectionRecommendation(
                section="skills",
                priority="high",
                issue=("The resume does not contain Kubernetes evidence."),
                recommendation=(
                    "Do not add Kubernetes unless the candidate has factual experience."
                ),
            )
        ],
        prioritized_actions=[
            "Place supported job keywords in prominent sections.",
            "Keep Kubernetes as a conditional recommendation.",
        ],
        warnings=[],
        rationale=("The proposed changes improve keyword placement without introducing new facts."),
    )


def test_prompt_contains_guardrails() -> None:
    prompt = ATS_OPTIMIZATION_SYSTEM_PROMPT.casefold()

    assert "never invent" in prompt
    assert "metrics" in prompt
    assert "safe keyword" in prompt
    assert "exact supporting resume excerpt" in prompt


def test_agent_input_builds_payload() -> None:
    request = build_request()
    baseline = build_ats_baseline(request)

    agent_input = ATSOptimizationAgentInput(
        request=request,
        baseline=baseline,
        validation_feedback=["A metric was unsupported."],
    )

    payload = agent_input.to_prompt_payload()

    assert "Kubernetes" in (payload["job_description_json"])
    assert "Python" in payload["resume_json"]
    assert "A metric was unsupported." in (payload["validation_feedback"])


def test_validator_accepts_grounded_output() -> None:
    validation = validate_ats_optimization_output(
        build_request(),
        valid_analysis(),
    )

    assert validation.is_valid is True
    assert validation.errors == []


def test_validator_rejects_fabricated_metric() -> None:
    analysis = valid_analysis()

    invalid_rewrite = analysis.bullet_rewrites[0].model_copy(
        update={
            "rewritten_text": (
                "Improved performance by 40% while deploying production backend services on AWS."
            )
        }
    )

    invalid_analysis = analysis.model_copy(update={"bullet_rewrites": [invalid_rewrite]})

    validation = validate_ats_optimization_output(
        build_request(),
        invalid_analysis,
    )

    assert validation.is_valid is False
    assert any("unsupported numeric" in error for error in validation.errors)


def test_validator_rejects_unsupported_skill() -> None:
    analysis = valid_analysis()
    summary = analysis.summary_rewrite

    assert summary is not None

    invalid_summary = summary.model_copy(
        update={
            "rewritten_summary": (
                "Backend engineer with Python, AWS, FastAPI, and Kubernetes experience."
            ),
            "keywords_added": [
                "FastAPI",
                "Kubernetes",
            ],
        }
    )

    invalid_analysis = analysis.model_copy(update={"summary_rewrite": invalid_summary})

    validation = validate_ats_optimization_output(
        build_request(),
        invalid_analysis,
    )

    assert validation.is_valid is False
    assert any("not supported by the resume" in error for error in validation.errors)
