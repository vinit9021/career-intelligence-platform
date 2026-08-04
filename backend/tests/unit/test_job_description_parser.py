import pytest

from app.parsers.job_description import (
    EmptyJobDescriptionError,
    JobDescriptionParser,
    JobDescriptionTooLargeError,
    normalize_job_description_text,
    parse_job_description,
)

FULL_JOB_DESCRIPTION = """
Job Title: Senior Backend Engineer
Company: Acme Technologies

Responsibilities:
- Design and maintain REST APIs using Python and FastAPI.
- Build scalable microservices on AWS.
- Collaborate with cross-functional teams.

Required Skills:
- Python
- FastAPI
- PostgreSQL
- Docker
- AWS
- Strong problem solving and communication skills

Preferred Skills:
- Kubernetes
- Redis
- Kafka

Qualifications:
- 4-6 years of backend engineering experience.
- Bachelor's degree in Computer Science or a related field.
- Experience with system design and CI/CD.
"""


def test_normalization_removes_controls_and_extra_space() -> None:
    normalized = normalize_job_description_text("  Senior\tEngineer\x00  \r\n\r\n  Python   SQL  ")

    assert normalized == ("Senior Engineer\n\nPython SQL")


@pytest.mark.parametrize(
    "text",
    ["", "   ", "\x00\x01\x02"],
)
def test_empty_input_is_rejected(
    text: str,
) -> None:
    with pytest.raises(EmptyJobDescriptionError):
        parse_job_description(text)


def test_oversized_input_is_rejected() -> None:
    parser = JobDescriptionParser(max_chars=10)

    with pytest.raises(JobDescriptionTooLargeError):
        parser.parse("x" * 11)


def test_complete_job_description_is_structured() -> None:
    result = parse_job_description(FULL_JOB_DESCRIPTION)

    assert result.job_title == ("Senior Backend Engineer")
    assert result.company_name == ("Acme Technologies")
    assert result.seniority_level == "senior"
    assert result.experience.min_years == 4
    assert result.experience.max_years == 6
    assert "Python" in result.required_skills
    assert "FastAPI" in result.required_skills
    assert "Kubernetes" in result.preferred_skills
    assert "AWS" in result.technologies
    assert "System Design" in result.ats_keywords
    assert len(result.responsibilities) == 3
    assert len(result.qualifications) == 3
    assert any("Bachelor's degree" in item for item in result.education_requirements)
    assert result.metadata.warnings == []


def test_preferred_skills_are_not_lost() -> None:
    result = parse_job_description(
        """
        Data Engineer
        Company: Example Labs

        Required Skills:
        - Python
        - SQL

        Preferred Skills:
        - Spark
        - Kafka

        Responsibilities:
        - Build data pipelines.

        Qualifications:
        - 3+ years of experience.
        """
    )

    assert result.required_skills == [
        "Python",
        "SQL",
    ]
    assert result.preferred_skills == [
        "Kafka",
        "Spark",
    ]


def test_missing_sections_generate_warnings() -> None:
    result = parse_job_description("Python and SQL are useful for this role.")

    assert result.job_title == ("Python and SQL are useful for this role.")
    assert result.company_name is None
    assert result.required_skills == [
        "Python",
        "SQL",
    ]
    assert {
        "Company name could not be identified.",
        "Responsibilities section was not found.",
        "Qualifications section was not found.",
    }.issubset(set(result.metadata.warnings))


def test_labeled_title_and_company_take_priority() -> None:
    result = parse_job_description(
        """
        Job Description
        Position: ML Engineer
        Organization: Vision Works

        Responsibilities:
        Build machine learning systems.

        Qualifications:
        2+ years of experience with Python and PyTorch.
        """
    )

    assert result.job_title == "ML Engineer"
    assert result.company_name == "Vision Works"
    assert result.experience.min_years == 2
    assert result.experience.max_years is None
    assert result.seniority_level == "unspecified"
    assert "Machine Learning" in result.ats_keywords
    assert "PyTorch" in result.technologies


def test_entry_level_seniority_is_detected() -> None:
    result = parse_job_description(
        """
        Junior Software Engineer
        Company: Starter Systems

        Responsibilities:
        Develop web services.

        Qualifications:
        Bachelor's degree preferred.
        """
    )

    assert result.seniority_level == "entry"


def test_result_is_serializable_structured_json() -> None:
    result = parse_job_description(FULL_JOB_DESCRIPTION)
    payload = result.model_dump(mode="json")

    assert payload["job_title"] == ("Senior Backend Engineer")
    assert payload["metadata"]["parser_version"] == ("1.0.0")
    assert payload["normalized_text"]


def test_company_is_extracted_from_recruiting_sentence() -> None:
    result = parse_job_description(
        """
        Software Engineer

        We Dolat Capital are looking for a Software
        Engineer with 2+ years of experience.

        Required Skills:
        - Python
        - FastAPI

        Responsibilities:
        - Develop backend APIs.
        """
    )

    assert result.company_name == "Dolat Capital"
    assert "Company name could not be identified." not in result.metadata.warnings
