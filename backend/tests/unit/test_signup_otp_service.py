from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.auth import RegisterRequest
from app.services.signup_otp import (
    SignupOtpExpiredError,
    SignupOtpInvalidError,
    SignupOtpRateLimitedError,
    SignupOtpService,
)


class MutableClock:
    def __init__(
        self,
    ) -> None:
        self.value = datetime(
            2026,
            8,
            11,
            tzinfo=UTC,
        )

    def __call__(
        self,
    ) -> datetime:
        return self.value

    def advance(
        self,
        *,
        seconds: int,
    ) -> None:
        self.value += timedelta(seconds=seconds)


def _payload() -> RegisterRequest:
    return RegisterRequest(
        email="User@Example.com",
        full_name="Test User",
        password="StrongPassword9!",
    )


@pytest.mark.asyncio
async def test_issue_and_verify_otp() -> None:
    clock = MutableClock()

    service = SignupOtpService(
        clock=clock,
        code_factory=lambda: "123456",
    )

    issued = await service.issue(
        _payload(),
        secret="secret",
    )

    assert issued.email == ("user@example.com")

    assert issued.code == "123456"

    registration = await service.verify(
        "USER@example.com",
        "123456",
        secret="secret",
    )

    assert str(registration.email) == "User@example.com"


@pytest.mark.asyncio
async def test_otp_request_rate_limit() -> None:
    service = SignupOtpService(
        code_factory=lambda: "123456",
    )

    await service.issue(
        _payload(),
        secret="secret",
    )

    with pytest.raises(SignupOtpRateLimitedError):
        await service.issue(
            _payload(),
            secret="secret",
        )


@pytest.mark.asyncio
async def test_otp_can_be_resent() -> None:
    clock = MutableClock()

    codes = iter(
        [
            "123456",
            "654321",
        ]
    )

    service = SignupOtpService(
        clock=clock,
        resend_seconds=60,
        code_factory=lambda: next(codes),
    )

    await service.issue(
        _payload(),
        secret="secret",
    )

    clock.advance(seconds=61)

    second = await service.issue(
        _payload(),
        secret="secret",
    )

    assert second.code == "654321"


@pytest.mark.asyncio
async def test_invalid_otp_tracks_attempts() -> None:
    service = SignupOtpService(
        max_attempts=2,
        code_factory=lambda: "123456",
    )

    await service.issue(
        _payload(),
        secret="secret",
    )

    with pytest.raises(SignupOtpInvalidError) as first:
        await service.verify(
            "user@example.com",
            "000000",
            secret="secret",
        )

    assert first.value.attempts_remaining == 1

    with pytest.raises(SignupOtpInvalidError) as second:
        await service.verify(
            "user@example.com",
            "000000",
            secret="secret",
        )

    assert second.value.attempts_remaining == 0

    with pytest.raises(SignupOtpExpiredError):
        await service.verify(
            "user@example.com",
            "123456",
            secret="secret",
        )


@pytest.mark.asyncio
async def test_expired_otp_is_rejected() -> None:
    clock = MutableClock()

    service = SignupOtpService(
        ttl_seconds=10,
        clock=clock,
        code_factory=lambda: "123456",
    )

    await service.issue(
        _payload(),
        secret="secret",
    )

    clock.advance(seconds=11)

    with pytest.raises(SignupOtpExpiredError):
        await service.verify(
            "user@example.com",
            "123456",
            secret="secret",
        )


@pytest.mark.asyncio
async def test_clear_removes_pending_otp() -> None:
    service = SignupOtpService(
        code_factory=lambda: "123456",
    )

    await service.issue(
        _payload(),
        secret="secret",
    )

    await service.clear("user@example.com")

    with pytest.raises(SignupOtpExpiredError):
        await service.verify(
            "user@example.com",
            "123456",
            secret="secret",
        )


def test_invalid_service_configuration() -> None:
    with pytest.raises(ValueError):
        SignupOtpService(ttl_seconds=0)

    with pytest.raises(ValueError):
        SignupOtpService(resend_seconds=-1)

    with pytest.raises(ValueError):
        SignupOtpService(max_attempts=0)


@pytest.mark.asyncio
async def test_invalid_code_factory() -> None:
    service = SignupOtpService(
        code_factory=lambda: "abc",
    )

    with pytest.raises(ValueError):
        await service.issue(
            _payload(),
            secret="secret",
        )
