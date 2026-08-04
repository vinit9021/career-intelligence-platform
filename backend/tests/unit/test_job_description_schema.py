import pytest
from pydantic import ValidationError

from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    ParsedJobDescription,
)


def test_structured_schema_defaults_are_safe() -> None:
    result = ParsedJobDescription(
        normalized_text="Backend Engineer",
        metadata=JobDescriptionParserMetadata(
            parser_name="test-parser",
            parser_version="1.0.0",
            character_count=16,
        ),
    )

    assert result.required_skills == []
    assert result.preferred_skills == []
    assert result.technologies == []
    assert result.seniority_level == "unspecified"
    assert result.metadata.warnings == []


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [(-1, None), (None, -1), (61, None)],
)
def test_invalid_experience_years_are_rejected(
    minimum: int | None,
    maximum: int | None,
) -> None:
    with pytest.raises(ValidationError):
        JobExperienceRequirement(
            min_years=minimum,
            max_years=maximum,
        )


def test_empty_normalized_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ParsedJobDescription(
            normalized_text="",
            metadata=JobDescriptionParserMetadata(
                parser_name="test-parser",
                parser_version="1.0.0",
                character_count=1,
            ),
        )
