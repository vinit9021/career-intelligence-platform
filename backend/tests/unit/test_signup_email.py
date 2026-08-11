from __future__ import annotations

from email.message import (
    EmailMessage,
)
from typing import (
    Any,
)

import pytest
from pydantic import (
    SecretStr,
)

from app.core.email_config import (
    SmtpSettings,
)
from app.services.signup_email import (
    EmailDeliveryError,
    SignupEmailService,
)


class FakeSMTP:
    sent_message: EmailMessage | None = None

    logged_in_user: str | None = None

    def __init__(
        self,
        host: str,
        port: int,
        *,
        timeout: int,
    ) -> None:
        assert host == "smtp.gmail.com"

        assert port == 587

        assert timeout == 20

    def __enter__(
        self,
    ) -> FakeSMTP:
        return self

    def __exit__(
        self,
        *args: Any,
    ) -> None:
        del args

    def ehlo(
        self,
    ) -> None:
        return None

    def starttls(
        self,
        *,
        context: Any,
    ) -> None:
        assert context is not None

    def login(
        self,
        username: str,
        password: str,
    ) -> None:
        self.__class__.logged_in_user = username

        assert password == "test-app-password"

    def send_message(
        self,
        message: EmailMessage,
    ) -> None:
        self.__class__.sent_message = message


def _settings() -> SmtpSettings:
    return SmtpSettings(
        smtp_host=("smtp.gmail.com"),
        smtp_port=587,
        smtp_username=("noreply.careerintelligence@gmail.com"),
        smtp_app_password=(SecretStr("test-app-password")),
        smtp_from_name=("Career Intelligence"),
        smtp_use_tls=True,
    )


@pytest.mark.asyncio
async def test_send_signup_otp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.signup_email.smtplib.SMTP",
        FakeSMTP,
    )

    service = SignupEmailService(_settings())

    await service.send_signup_otp(
        recipient=("user@example.com"),
        otp="123456",
        expires_in=600,
    )

    message = FakeSMTP.sent_message

    assert message is not None

    assert message["To"] == "user@example.com"

    assert "123456" in message["Subject"]

    assert FakeSMTP.logged_in_user == ("noreply.careerintelligence@gmail.com")


@pytest.mark.asyncio
async def test_email_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_smtp(
        *args: Any,
        **kwargs: Any,
    ) -> None:
        del args
        del kwargs

        raise OSError("SMTP unavailable")

    monkeypatch.setattr(
        "app.services.signup_email.smtplib.SMTP",
        fail_smtp,
    )

    service = SignupEmailService(_settings())

    with pytest.raises(EmailDeliveryError):
        await service.send_signup_otp(
            recipient=("user@example.com"),
            otp="123456",
            expires_in=600,
        )
