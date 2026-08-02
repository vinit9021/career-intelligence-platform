from app.db.base import Base
from app.models import Profile


def test_profile_model_is_registered() -> None:
    assert Profile.__tablename__ == "profiles"
    assert "profiles" in Base.metadata.tables


def test_profile_table_has_required_columns() -> None:
    table = Base.metadata.tables["profiles"]

    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "headline",
        "location",
        "phone",
        "bio",
        "years_experience",
        "target_roles",
        "skills",
        "linkedin_url",
        "github_url",
        "portfolio_url",
        "created_at",
        "updated_at",
    }

    assert table.c.id.primary_key is True
    assert table.c.user_id.nullable is False
    assert table.c.user_id.unique is True
    assert table.c.target_roles.nullable is False
    assert table.c.skills.nullable is False


def test_profile_references_user_with_cascade() -> None:
    table = Base.metadata.tables["profiles"]
    foreign_keys = table.c.user_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_profile_has_experience_constraint() -> None:
    table = Base.metadata.tables["profiles"]

    constraint_names = {
        constraint.name for constraint in table.constraints if constraint.name is not None
    }

    assert "ck_profiles_years_experience_range" in constraint_names
