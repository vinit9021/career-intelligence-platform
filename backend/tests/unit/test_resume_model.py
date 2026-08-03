from app.db.base import Base
from app.models import Resume


def test_resume_model_is_registered() -> None:
    assert Resume.__tablename__ == "resumes"
    assert "resumes" in Base.metadata.tables


def test_resume_table_has_required_columns() -> None:
    table = Base.metadata.tables["resumes"]

    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "original_filename",
        "storage_backend",
        "storage_key",
        "storage_etag",
        "content_type",
        "file_extension",
        "file_size_bytes",
        "sha256",
        "parse_status",
        "parse_error",
        "parsed_at",
        "created_at",
    }

    assert table.c.id.primary_key is True
    assert table.c.user_id.nullable is False
    assert table.c.storage_key.unique is True


def test_resume_references_user_with_cascade() -> None:
    table = Base.metadata.tables["resumes"]
    foreign_keys = table.c.user_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_resume_constraints_are_registered() -> None:
    table = Base.metadata.tables["resumes"]

    constraint_names = {
        constraint.name for constraint in table.constraints if constraint.name is not None
    }

    assert "ck_resumes_positive_file_size" in constraint_names
    assert "ck_resumes_file_extension_valid" in constraint_names
    assert "ck_resumes_storage_backend_valid" in constraint_names
