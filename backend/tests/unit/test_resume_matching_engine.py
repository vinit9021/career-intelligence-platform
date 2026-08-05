from app.matching import (
    ResumeJobMatcher,
    match_resume_to_job,
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


def build_job(
    **overrides: object,
) -> ParsedJobDescription:
    data: dict[str, object] = {
        "job_title": "Backend Engineer",
        "company_name": "Example Labs",
        "required_skills": [
            "Python",
            "FastAPI",
            "PostgreSQL",
        ],
        "preferred_skills": [
            "Docker",
            "AWS",
        ],
        "technologies": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
            "AWS",
        ],
        "responsibilities": [
            "Develop REST APIs using FastAPI",
            "Design PostgreSQL data models",
        ],
        "qualifications": [],
        "experience": JobExperienceRequirement(
            min_years=2,
            statement="2+ years of experience",
        ),
        "education_requirements": [
            "Bachelor's degree in Computer Science",
        ],
        "seniority_level": "mid",
        "ats_keywords": [
            "Python",
            "REST APIs",
            "Postgres",
            "AWS",
        ],
        "normalized_text": (
            "Backend Engineer requiring Python, FastAPI, PostgreSQL, Docker and AWS."
        ),
        "metadata": JobDescriptionParserMetadata(
            parser_name="test_parser",
            parser_version="1.0.0",
            character_count=80,
        ),
    }
    data.update(overrides)
    return ParsedJobDescription.model_validate(data)


def build_resume(
    **overrides: object,
) -> ResumeStructuredContent:
    data: dict[str, object] = {
        "summary": ("Backend engineer with 3 years of experience."),
        "skills": [
            "Python",
            "FastAPI",
            "Postgres",
            "Docker",
            "Amazon Web Services",
        ],
        "education": [
            "B.Tech in Computer Science",
        ],
        "experience": [
            "Developed REST APIs using FastAPI and Python.",
            "Designed PostgreSQL schemas for production services.",
        ],
        "projects": [],
        "certifications": [],
    }
    data.update(overrides)
    return ResumeStructuredContent.model_validate(data)


def test_perfect_match_scores_highly() -> None:
    result = match_resume_to_job(
        resume=build_resume(),
        job_description=build_job(),
        reference_year=2026,
    )

    assert result.overall_match_score >= 90
    assert result.required_skills_score == 100
    assert result.preferred_skills_score == 100
    assert result.technology_score == 100
    assert result.experience.status == "met"
    assert result.education.status == "met"
    assert result.missing_required_skills == []
    assert result.strengths


def test_partial_match_reports_missing_requirements() -> None:
    resume = build_resume(
        skills=["Python", "FastAPI"],
        experience=["Built FastAPI endpoints for an internal tool."],
        education=[],
    )

    result = match_resume_to_job(
        resume=resume,
        job_description=build_job(),
        candidate_experience_years=1.5,
    )

    assert 0 < result.overall_match_score < 90
    assert "PostgreSQL" in result.missing_required_skills
    assert "Docker" in result.missing_preferred_skills
    assert result.experience.status == "partially_met"
    assert result.education.status == "unknown"
    assert result.weaknesses


def test_no_match_remains_within_score_bounds() -> None:
    result = match_resume_to_job(
        resume=build_resume(
            summary=None,
            skills=["MATLAB"],
            education=["Diploma in Electronics"],
            experience=["Designed analog circuits."],
        ),
        job_description=build_job(),
        candidate_experience_years=0,
    )

    assert 0 <= result.overall_match_score <= 100
    assert result.required_skills_score == 0
    assert set(result.missing_required_skills) == {
        "Python",
        "FastAPI",
        "PostgreSQL",
    }
    assert result.experience.status == "not_met"
    assert result.responsibility_score < 40


def test_aliases_match_canonical_technologies() -> None:
    job = build_job(
        required_skills=[
            "PostgreSQL",
            "AWS",
            "JavaScript",
            "Kubernetes",
        ],
        preferred_skills=[],
        technologies=[],
        responsibilities=[],
        ats_keywords=[],
        education_requirements=[],
        experience=JobExperienceRequirement(),
    )
    resume = build_resume(
        skills=[
            "Postgres",
            "Amazon Web Services",
            "JS",
            "k8s",
        ]
    )

    result = match_resume_to_job(
        resume=resume,
        job_description=job,
    )

    assert result.required_skills_score == 100
    assert result.missing_required_skills == []
    assert len(result.resume_evidence) == 4


def test_experience_is_estimated_from_date_ranges() -> None:
    job = build_job(
        required_skills=[],
        preferred_skills=[],
        technologies=[],
        responsibilities=[],
        ats_keywords=[],
        education_requirements=[],
        experience=JobExperienceRequirement(
            min_years=4,
            statement="4+ years",
        ),
    )
    resume = build_resume(
        summary=None,
        skills=[],
        experience=[
            "Software Engineer | 2021 - Present",
        ],
    )

    result = match_resume_to_job(
        resume=resume,
        job_description=job,
        reference_year=2026,
    )

    assert result.experience.candidate_years == 5
    assert result.experience.status == "met"
    assert result.overall_match_score == 100


def test_unknown_experience_generates_warning() -> None:
    result = match_resume_to_job(
        resume=build_resume(
            summary=None,
            experience=[],
        ),
        job_description=build_job(),
    )

    assert result.experience.status == "unknown"
    assert any("Experience alignment is uncertain" in warning for warning in result.warnings)


def test_higher_degree_satisfies_lower_degree_requirement() -> None:
    job = build_job(
        required_skills=[],
        preferred_skills=[],
        technologies=[],
        responsibilities=[],
        ats_keywords=[],
        experience=JobExperienceRequirement(),
        education_requirements=[
            "Bachelor's degree in Computer Science",
        ],
    )
    resume = build_resume(
        skills=[],
        education=[
            "Master of Technology in Computer Science",
        ],
    )

    result = match_resume_to_job(
        resume=resume,
        job_description=job,
    )

    assert result.education.status == "met"
    assert result.education.score == 100


def test_responsibility_alignment_contains_evidence() -> None:
    result = match_resume_to_job(
        resume=build_resume(),
        job_description=build_job(),
    )

    assert len(result.responsibility_alignment) == 2
    assert all(
        item.status
        in {
            "aligned",
            "partially_aligned",
        }
        for item in result.responsibility_alignment
    )
    assert all(item.evidence is not None for item in result.responsibility_alignment)


def test_missing_requirements_are_not_scored_as_failures() -> None:
    job = build_job(
        required_skills=[],
        preferred_skills=[],
        technologies=[],
        responsibilities=[],
        ats_keywords=[],
        education_requirements=[],
        experience=JobExperienceRequirement(),
    )

    result = match_resume_to_job(
        resume=build_resume(),
        job_description=job,
    )

    assert result.overall_match_score == 0
    assert all(item.applicable is False for item in result.scoring_breakdown)
    assert any("no matchable requirements" in warning.casefold() for warning in result.warnings)


def test_output_is_deterministic() -> None:
    request = ResumeJobMatchRequest(
        resume=build_resume(),
        job_description=build_job(),
    )
    matcher = ResumeJobMatcher(reference_year=2026)

    first = matcher.match(request)
    second = matcher.match(request)

    assert first.model_dump() == second.model_dump()


def test_effective_weights_sum_to_one() -> None:
    result = match_resume_to_job(
        resume=build_resume(),
        job_description=build_job(),
    )
    applicable = [item for item in result.scoring_breakdown if item.applicable]

    assert (
        round(
            sum(item.effective_weight for item in applicable),
            3,
        )
        == 1.0
    )
