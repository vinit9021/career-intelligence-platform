import pytest
from pydantic import ValidationError

from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    ParsedJobDescription,
)
from app.schemas.resume_matching import (
    MatchCategoryScore,
    ResumeJobMatchRequest,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)


def build_request() -> ResumeJobMatchRequest:
    return ResumeJobMatchRequest(
        resume=ResumeStructuredContent(
            skills=["Python"],
        ),
        job_description=ParsedJobDescription(
            required_skills=["Python"],
            normalized_text="Python developer",
            metadata=JobDescriptionParserMetadata(
                parser_name="test",
                parser_version="1.0.0",
                character_count=16,
            ),
        ),
    )


def test_request_accepts_parsed_models() -> None:
    request = build_request()

    assert request.resume.skills == ["Python"]
    assert request.job_description.required_skills == ["Python"]


def test_candidate_experience_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ResumeJobMatchRequest(
            resume=ResumeStructuredContent(),
            job_description=build_request().job_description,
            candidate_experience_years=-1,
        )


def test_category_score_rejects_out_of_range_score() -> None:
    with pytest.raises(ValidationError):
        MatchCategoryScore(
            category="required_skills",
            raw_score=101,
            configured_weight=0.3,
            effective_weight=1.0,
            weighted_points=101,
            applicable=True,
            explanation="invalid",
        )
