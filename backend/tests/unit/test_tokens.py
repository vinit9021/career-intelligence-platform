from uuid import uuid4

import pytest

from app.core.config import Settings
from app.security.tokens import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)


def build_settings() -> Settings:
    return Settings.model_validate(
        {
            "postgres_host": "unused",
            "postgres_db": "unused",
            "postgres_user": "unused",
            "postgres_password": "unused",
            "jwt_access_secret": "a" * 64,
            "jwt_refresh_secret": "b" * 64,
            "jwt_issuer": "test-issuer",
            "jwt_audience": "test-audience",
        }
    )


def test_token_claims_are_created() -> None:
    settings = build_settings()
    user_id = uuid4()

    access_token = create_access_token(
        user_id,
        settings,
    )

    refresh_token = create_refresh_token(
        user_id,
        settings,
    )

    access_claims = decode_token(
        access_token.value,
        "access",
        settings,
    )

    refresh_claims = decode_token(
        refresh_token.value,
        "refresh",
        settings,
    )

    assert access_claims.sub == user_id
    assert access_claims.jti == access_token.jti
    assert access_claims.type == "access"

    assert refresh_claims.sub == user_id
    assert refresh_claims.jti == refresh_token.jti
    assert refresh_claims.type == "refresh"


def test_token_type_and_signature_are_validated() -> None:
    settings = build_settings()

    access_token = create_access_token(
        uuid4(),
        settings,
    )

    with pytest.raises(TokenValidationError):
        decode_token(
            access_token.value,
            "refresh",
            settings,
        )

    with pytest.raises(TokenValidationError):
        decode_token(
            access_token.value + "tampered",
            "access",
            settings,
        )


def test_refresh_token_hash_is_deterministic() -> None:
    token = "refresh-token-value"

    assert hash_token(token) == hash_token(token)
    assert len(hash_token(token)) == 64
