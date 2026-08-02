from app.db.base import Base
from app.models import RefreshToken, User


def test_authentication_models_are_registered() -> None:
    assert User.__tablename__ == "users"
    assert RefreshToken.__tablename__ == "refresh_tokens"

    assert "users" in Base.metadata.tables
    assert "refresh_tokens" in Base.metadata.tables


def test_user_table_contains_required_columns() -> None:
    table = Base.metadata.tables["users"]

    assert set(table.columns.keys()) == {
        "id",
        "email",
        "password_hash",
        "full_name",
        "is_active",
        "is_verified",
        "created_at",
        "updated_at",
    }

    assert table.c.id.primary_key is True
    assert table.c.email.nullable is False
    assert table.c.email.unique is True
    assert table.c.password_hash.nullable is False


def test_refresh_token_table_contains_required_columns() -> None:
    table = Base.metadata.tables["refresh_tokens"]

    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "jti",
        "token_hash",
        "expires_at",
        "revoked_at",
        "created_at",
    }

    assert table.c.id.primary_key is True
    assert table.c.user_id.nullable is False
    assert table.c.jti.unique is True
    assert table.c.token_hash.unique is True


def test_refresh_token_references_user_with_cascade_delete() -> None:
    table = Base.metadata.tables["refresh_tokens"]
    foreign_keys = table.c.user_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"
