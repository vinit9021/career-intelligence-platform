from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError
from pydantic import BaseModel, ValidationError

from app.core.config import Settings

TokenType = Literal["access", "refresh"]


class TokenClaims(BaseModel):
    sub: UUID
    jti: UUID
    type: TokenType
    iat: datetime
    nbf: datetime
    exp: datetime
    iss: str
    aud: str


@dataclass(frozen=True, slots=True)
class EncodedToken:
    value: str
    jti: UUID
    expires_at: datetime


class TokenValidationError(ValueError):
    pass


def _secret_for(
    token_type: TokenType,
    settings: Settings,
) -> str:
    secret = settings.jwt_access_secret if token_type == "access" else settings.jwt_refresh_secret

    return secret.get_secret_value()


def _create_token(
    user_id: UUID,
    token_type: TokenType,
    settings: Settings,
) -> EncodedToken:
    now = datetime.now(UTC)

    lifetime = (
        timedelta(
            minutes=settings.access_token_expire_minutes,
        )
        if token_type == "access"
        else timedelta(
            days=settings.refresh_token_expire_days,
        )
    )

    expires_at = now + lifetime
    jti = uuid4()

    payload = {
        "sub": str(user_id),
        "jti": str(jti),
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    encoded = jwt.encode(
        payload,
        _secret_for(token_type, settings),
        algorithm=settings.jwt_algorithm,
    )

    return EncodedToken(
        value=encoded,
        jti=jti,
        expires_at=expires_at,
    )


def create_access_token(
    user_id: UUID,
    settings: Settings,
) -> EncodedToken:
    return _create_token(
        user_id=user_id,
        token_type="access",
        settings=settings,
    )


def create_refresh_token(
    user_id: UUID,
    settings: Settings,
) -> EncodedToken:
    return _create_token(
        user_id=user_id,
        token_type="refresh",
        settings=settings,
    )


def decode_token(
    token: str,
    expected_type: TokenType,
    settings: Settings,
) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            _secret_for(expected_type, settings),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require": [
                    "sub",
                    "jti",
                    "type",
                    "iat",
                    "nbf",
                    "exp",
                    "iss",
                    "aud",
                ]
            },
        )

        claims = TokenClaims.model_validate(payload)
    except (InvalidTokenError, ValidationError) as exc:
        raise TokenValidationError("Token is invalid or expired.") from exc

    if claims.type != expected_type:
        raise TokenValidationError("Token type is invalid.")

    return claims


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
