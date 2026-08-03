from app.db.base import Base
from app.models import Resume, ResumeParseResult


def test_resume_parse_result_model_is_registered() -> None:
    assert ResumeParseResult.__tablename__ == "resume_parse_results"
    assert "resume_parse_results" in Base.metadata.tables


def test_resume_contains_parsing_state_columns() -> None:
    table = Base.metadata.tables[Resume.__tablename__]

    assert "parse_status" in table.columns
    assert "parse_error" in table.columns
    assert "parsed_at" in table.columns


def test_parse_result_references_resume_with_cascade() -> None:
    table = Base.metadata.tables[ResumeParseResult.__tablename__]
    foreign_key = next(iter(table.c.resume_id.foreign_keys))

    assert foreign_key.target_fullname == "resumes.id"
    assert foreign_key.ondelete == "CASCADE"
    assert table.c.resume_id.unique is True
