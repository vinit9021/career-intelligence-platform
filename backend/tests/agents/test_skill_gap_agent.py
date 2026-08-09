"""Tests for Skill Gap AI Agent."""

from app.agents.skill_gap.state import (
    LearningRoadmapStep,
    MiniProjectRecommendation,
    SkillGapAnalysis,
    SkillGapItem,
    SkillGapRequest,
)
from app.agents.skill_gap.validator import (
    validate_skill_gap_output,
)
from app.matching import match_resume_to_job
from app.prompts.skill_gap import (
    SKILL_GAP_SYSTEM_PROMPT,
)
from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    ParsedJobDescription,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)
from app.skill_gap.analyzer import (
    build_skill_gap_baseline,
)


def build_request() -> SkillGapRequest:
    resume = ResumeStructuredContent.model_validate(
        {
            "summary": ("Backend engineer with Python, FastAPI, and AWS experience."),
            "skills": [
                "Python",
                "FastAPI",
                "AWS",
            ],
            "experience": [("Built backend APIs using Python and FastAPI.")],
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
            "Kubernetes",
        ],
        preferred_skills=[
            "Redis",
        ],
        technologies=[
            "FastAPI",
            "Docker",
            "Kubernetes",
        ],
        responsibilities=[("Build and deploy scalable backend services.")],
        qualifications=[],
        experience=(JobExperienceRequirement()),
        education_requirements=[],
        seniority_level="unspecified",
        ats_keywords=[
            "Python",
            "FastAPI",
            "Docker",
            "Kubernetes",
            "Redis",
        ],
        normalized_text=(
            "Example Labs needs a Backend Engineer "
            "with Python, Kubernetes, Docker, "
            "FastAPI and Redis."
        ),
        metadata=(
            JobDescriptionParserMetadata(
                parser_name="test",
                parser_version="1.0.0",
                character_count=120,
            )
        ),
    )

    raw_text = (
        "Backend engineer with Python, FastAPI, "
        "and AWS experience. Built backend APIs "
        "using Python and FastAPI."
    )

    match_result = match_resume_to_job(
        resume=resume,
        job_description=job,
        resume_raw_text=raw_text,
    )

    return SkillGapRequest(
        resume=resume,
        job_description=job,
        match_result=match_result,
        resume_raw_text=raw_text,
        max_roadmap_steps=5,
        max_mini_projects=2,
    )


def valid_analysis() -> SkillGapAnalysis:
    return SkillGapAnalysis(
        gap_score=70,
        gaps=[
            SkillGapItem(
                skill="Kubernetes",
                category="required_skill",
                priority="critical",
                reason=("Required by the target role."),
                jd_evidence="Kubernetes",
                difficulty="intermediate",
                estimated_effort="medium",
            ),
            SkillGapItem(
                skill="Docker",
                category="technology",
                priority="high",
                reason=("Used by the target role."),
                jd_evidence="Docker",
                difficulty="intermediate",
                estimated_effort="short",
            ),
            SkillGapItem(
                skill="Redis",
                category="preferred_skill",
                priority="medium",
                reason=("Preferred by the target role."),
                jd_evidence="Redis",
                difficulty="beginner",
                estimated_effort="short",
            ),
        ],
        learning_roadmap=[
            LearningRoadmapStep(
                order=1,
                target_skill="Docker",
                topics=[
                    "Containers",
                    "Images",
                ],
                exercises=[("Containerize a small backend service.")],
                completion_signal=("Run the service successfully inside a container."),
            ),
            LearningRoadmapStep(
                order=2,
                target_skill="Kubernetes",
                topics=[
                    "Pods",
                    "Deployments",
                    "Services",
                ],
                exercises=[("Deploy a containerized application locally.")],
                completion_signal=("Deploy and expose a working application."),
            ),
        ],
        mini_projects=[
            MiniProjectRecommendation(
                title=("Container Deployment Lab"),
                target_skills=[
                    "Docker",
                    "Kubernetes",
                ],
                description=("Package and deploy a small backend application."),
                deliverables=[
                    "Container configuration",
                    "Deployment manifests",
                    "README",
                ],
            )
        ],
        warnings=[],
        summary=("Prioritize Kubernetes and Docker, then learn Redis."),
    )


def test_prompt_contains_guardrails() -> None:
    prompt = SKILL_GAP_SYSTEM_PROMPT.casefold()

    assert "never classify a skill as missing" in prompt

    assert "exact supporting job-description" in prompt

    assert "never invent candidate experience" in prompt


def test_validator_accepts_valid_gaps() -> None:
    request = build_request()

    baseline = build_skill_gap_baseline(request)

    result = validate_skill_gap_output(
        request,
        baseline,
        valid_analysis(),
    )

    assert result.is_valid is True


def test_validator_rejects_false_gap() -> None:
    request = build_request()

    baseline = build_skill_gap_baseline(request)

    analysis = valid_analysis()

    invalid = analysis.model_copy(
        update={
            "gaps": [
                *analysis.gaps,
                SkillGapItem(
                    skill="Python",
                    category="required_skill",
                    priority="critical",
                    reason="Missing Python.",
                    jd_evidence="Python",
                ),
            ]
        }
    )

    result = validate_skill_gap_output(
        request,
        baseline,
        invalid,
    )

    assert result.is_valid is False

    assert any("false or unsupported skill gap" in error for error in result.errors)


def test_validator_rejects_unrelated_project_skill() -> None:
    request = build_request()

    baseline = build_skill_gap_baseline(request)

    analysis = valid_analysis()

    invalid = analysis.model_copy(
        update={
            "mini_projects": [
                MiniProjectRecommendation(
                    title="React Project",
                    target_skills=["React"],
                    description=("Build a React project."),
                    deliverables=["Working project"],
                )
            ]
        }
    )

    result = validate_skill_gap_output(
        request,
        baseline,
        invalid,
    )

    assert result.is_valid is False

    assert any("not a validated gap" in error for error in result.errors)
