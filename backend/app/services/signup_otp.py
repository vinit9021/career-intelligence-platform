from __future__ import annotations

import asyncio
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.schemas.auth import RegisterRequest


class SignupOtpError(Exception):
    """Base signup OTP error."""


class SignupOtpInvalidError(SignupOtpError):
    def __init__(
        self,
        attempts_remaining: int,
    ) -> None:
        self.attempts_remaining = attempts_remaining
        super().__init__("The verification code is invalid.")


class SignupOtpExpiredError(SignupOtpError):
    """The OTP is missing or has expired."""


class SignupOtpRateLimitedError(SignupOtpError):
    def __init__(
        self,
        retry_after: int,
    ) -> None:
        self.retry_after = retry_after
        super().__init__("A new verification code cannot be requested yet.")


@dataclass(
    frozen=True,
    slots=True,
)
class SignupOtpIssueResult:
    email: str
    code: str
    expires_in: int
    resend_in: int


@dataclass(
    slots=True,
)
class _PendingSignup:
    payload: RegisterRequest
    otp_digest: str
    expires_at: datetime
    resend_at: datetime
    attempts_remaining: int


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class SignupOtpService:
    def __init__(
        self,
        *,
        ttl_seconds: int = 600,
        resend_seconds: int = 60,
        max_attempts: int = 5,
        clock: Callable[[], datetime] = _utc_now,
        code_factory: Callable[[], str] = _generate_code,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive.")

        if resend_seconds < 0:
            raise ValueError("resend_seconds cannot be negative.")

        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")

        self._ttl_seconds = ttl_seconds
        self._resend_seconds = resend_seconds
        self._max_attempts = max_attempts
        self._clock = clock
        self._code_factory = code_factory

        self._pending: dict[
            str,
            _PendingSignup,
        ] = {}

        self._lock = asyncio.Lock()

    @staticmethod
    def _digest(
        code: str,
        secret: str,
    ) -> str:
        return hmac.new(
            secret.encode("utf-8"),
            code.encode("utf-8"),
            sha256,
        ).hexdigest()

    async def issue(
        self,
        payload: RegisterRequest,
        *,
        secret: str,
    ) -> SignupOtpIssueResult:
        email = str(payload.email).lower()

        now = self._clock()

        async with self._lock:
            existing = self._pending.get(email)

            if existing is not None and now < existing.resend_at:
                retry_after = max(
                    1,
                    int((existing.resend_at - now).total_seconds()),
                )

                raise SignupOtpRateLimitedError(retry_after)

            code = self._code_factory()

            if len(code) != 6 or not code.isdigit():
                raise ValueError("OTP generator must return exactly six digits.")

            self._pending[email] = _PendingSignup(
                payload=payload,
                otp_digest=self._digest(
                    code,
                    secret,
                ),
                expires_at=(now + timedelta(seconds=self._ttl_seconds)),
                resend_at=(now + timedelta(seconds=self._resend_seconds)),
                attempts_remaining=(self._max_attempts),
            )

        return SignupOtpIssueResult(
            email=email,
            code=code,
            expires_in=self._ttl_seconds,
            resend_in=self._resend_seconds,
        )

    async def verify(
        self,
        email: str,
        otp: str,
        *,
        secret: str,
    ) -> RegisterRequest:
        normalized_email = email.strip().lower()

        now = self._clock()

        async with self._lock:
            pending = self._pending.get(normalized_email)

            if pending is None:
                raise SignupOtpExpiredError

            if now >= pending.expires_at:
                self._pending.pop(
                    normalized_email,
                    None,
                )
                raise SignupOtpExpiredError

            supplied_digest = self._digest(
                otp,
                secret,
            )

            if not hmac.compare_digest(
                supplied_digest,
                pending.otp_digest,
            ):
                pending.attempts_remaining -= 1

                attempts_remaining = pending.attempts_remaining

                if attempts_remaining <= 0:
                    self._pending.pop(
                        normalized_email,
                        None,
                    )

                raise SignupOtpInvalidError(
                    max(
                        attempts_remaining,
                        0,
                    )
                )

            payload = pending.payload

            self._pending.pop(
                normalized_email,
                None,
            )

            return payload

    async def clear(
        self,
        email: str,
    ) -> None:
        async with self._lock:
            self._pending.pop(
                email.strip().lower(),
                None,
            )
