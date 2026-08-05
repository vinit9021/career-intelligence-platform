"""Tests for the Resume Matching AI Agent."""

from app.agents.resume_matching.state import (
    ResumeMatchingAgentInput,
    SemanticRequirementEvidence,
    SemanticResponsibilityAssessment,
    SemanticResumeMatchingAnalysis,
)
from app.agents.resume_matching.validator import (
    validate_semantic_match_output,
)
from app.matching import match_resume_to_job
from app.prompts.resume_matching import (
    RESUME_MATCHING_SYSTEM_PROMPT,
)
from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    ParsedJobDescription,
)
from app.schemas.resume_matching import (
    ResumeJobMatchRequest,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)


def build_request() -> ResumeJobMatchRequest:
    resume = ResumeStructuredContent.model_validate(
        {
            "summary": "Backend engineer.",
            "skills": [
                "Python",
                "AWS",
            ],
            "experience": [("Deployed backend services on AWS for production workloads.")],
            "education": [],
            "projects": [],
            "certifications": [],
        }
    )

    job = ParsedJobDescription(
        job_title="Backend Engineer",
        company_name="Example Labs",
        required_skills=[
            "Python",
            "Cloud deployment",
        ],
        preferred_skills=[],
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
            "Cloud deployment",
        ],
        normalized_text=("Backend Engineer requiring Python, AWS and cloud deployment."),
        metadata=JobDescriptionParserMetadata(
            parser_name="test",
            parser_version="1.0.0",
            character_count=80,
        ),
    )

    return ResumeJobMatchRequest(
        resume=resume,
        job_description=job,
        resume_raw_text=("Deployed backend services on AWS for production workloads."),
    )


def build_analysis() -> SemanticResumeMatchingAnalysis:
    return SemanticResumeMatchingAnalysis(
        overall_semantic_score=85,
        semantic_requirement_evidence=[
            SemanticRequirementEvidence(
                requirement="Cloud deployment",
                resume_excerpt=("Deployed backend services on AWS for production workloads."),
                source_section="experience",
                explanation=("Deploying production services on AWS demonstrates cloud deployment."),
                confidence=0.9,
            )
        ],
        responsibility_alignment=[
            SemanticResponsibilityAssessment.model_validate(
                {
                    "responsibility": ("Deploy backend services to cloud infrastructure"),
                    "status": "aligned",
                    "score": 90,
                    "resume_excerpt": (
                        "Deployed backend services on AWS for production workloads."
                    ),
                    "explanation": ("The resume directly describes cloud backend deployment."),
                }
            )
        ],
        strengths=["Strong backend cloud deployment evidence."],
        weaknesses=[],
        warnings=[],
        summary=("The resume aligns well with the backend cloud requirements."),
    )


def test_prompt_forbids_fabrication() -> None:
    prompt = RESUME_MATCHING_SYSTEM_PROMPT.casefold()

    assert "never invent" in prompt
    assert "exact excerpt" in prompt
    assert "semantic equivalence" in prompt


def test_agent_input_builds_payload() -> None:
    request = build_request()

    baseline = match_resume_to_job(
        resume=request.resume,
        job_description=request.job_description,
        resume_raw_text=request.resume_raw_text,
    )

    agent_input = ResumeMatchingAgentInput(
        request=request,
        baseline_result=baseline,
        validation_feedback=["Evidence was unsupported."],
    )

    payload = agent_input.to_prompt_payload()

    assert "Cloud deployment" in (payload["job_description_json"])
    assert "AWS" in payload["resume_json"]
    assert "Evidence was unsupported." in (payload["validation_feedback"])


def test_validator_accepts_supported_evidence() -> None:
    validation = validate_semantic_match_output(
        build_request(),
        build_analysis(),
    )

    assert validation.is_valid is True
    assert validation.errors == []


def test_validator_rejects_fake_excerpt() -> None:
    analysis = build_analysis()

    invalid_evidence = analysis.semantic_requirement_evidence[0].model_copy(
        update={"resume_excerpt": ("Managed Kubernetes clusters.")}
    )

    invalid_analysis = analysis.model_copy(
        update={"semantic_requirement_evidence": [invalid_evidence]}
    )

    validation = validate_semantic_match_output(
        build_request(),
        invalid_analysis,
    )

    assert validation.is_valid is False
    assert any("not supported by the resume" in error for error in validation.errors)
