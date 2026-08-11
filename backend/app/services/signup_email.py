from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.message import (
    EmailMessage,
)
from email.utils import (
    formataddr,
)

from app.core.email_config import (
    SmtpSettings,
)


class EmailDeliveryError(RuntimeError):
    """Raised when an OTP email cannot be delivered."""


class SignupEmailService:
    def __init__(
        self,
        settings: SmtpSettings,
    ) -> None:
        self._settings = settings

    async def send_signup_otp(
        self,
        *,
        recipient: str,
        otp: str,
        expires_in: int,
    ) -> None:
        await asyncio.to_thread(
            self._send_signup_otp,
            recipient,
            otp,
            expires_in,
        )

    def _send_signup_otp(
        self,
        recipient: str,
        otp: str,
        expires_in: int,
    ) -> None:
        message = self._build_message(
            recipient=recipient,
            otp=otp,
            expires_in=(expires_in),
        )

        settings = self._settings

        try:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=(settings.smtp_timeout_seconds),
            ) as smtp:
                smtp.ehlo()

                if settings.smtp_use_tls:
                    context = ssl.create_default_context()

                    smtp.starttls(context=context)

                    smtp.ehlo()

                smtp.login(
                    str(settings.smtp_username),
                    settings.smtp_app_password.get_secret_value(),
                )

                smtp.send_message(message)

        except (
            OSError,
            smtplib.SMTPException,
        ) as exc:
            raise EmailDeliveryError("Unable to deliver signup OTP email.") from exc

    def _build_message(
        self,
        *,
        recipient: str,
        otp: str,
        expires_in: int,
    ) -> EmailMessage:
        minutes = max(
            1,
            expires_in // 60,
        )

        message = EmailMessage()

        message["Subject"] = f"{otp} is your Career Intelligence verification code"

        message["From"] = formataddr(
            (
                self._settings.smtp_from_name,
                str(self._settings.smtp_username),
            )
        )

        message["To"] = recipient

        message.set_content(
            "Career Intelligence\n\n"
            "Verify your email address\n\n"
            f"Your verification code is: {otp}\n\n"
            f"This code expires in {minutes} minutes.\n\n"
            "If you did not create a Career Intelligence "
            "account, you can safely ignore this email.\n\n"
            "Career Intelligence"
        )

        message.add_alternative(
            f"""
            <!doctype html>
            <html>
              <body
                style="
                  margin:0;
                  padding:0;
                  background:#f8fafc;
                  font-family:Arial,Helvetica,sans-serif;
                  color:#0f172a;
                "
              >
                <div
                  style="
                    max-width:560px;
                    margin:40px auto;
                    padding:0 20px;
                  "
                >
                  <div
                    style="
                      background:#ffffff;
                      border:1px solid #e2e8f0;
                      border-radius:18px;
                      padding:36px;
                    "
                  >
                    <div
                      style="
                        width:44px;
                        height:44px;
                        line-height:44px;
                        text-align:center;
                        border-radius:12px;
                        background:#4f46e5;
                        color:#ffffff;
                        font-weight:700;
                        margin-bottom:24px;
                      "
                    >
                      CI
                    </div>

                    <h1
                      style="
                        margin:0;
                        font-size:24px;
                        color:#0f172a;
                      "
                    >
                      Verify your email
                    </h1>

                    <p
                      style="
                        margin:14px 0 0;
                        color:#64748b;
                        font-size:15px;
                        line-height:24px;
                      "
                    >
                      Use the following code to complete
                      your Career Intelligence account
                      registration.
                    </p>

                    <div
                      style="
                        margin:28px 0;
                        padding:20px;
                        border-radius:14px;
                        background:#eef2ff;
                        color:#312e81;
                        text-align:center;
                        font-size:30px;
                        letter-spacing:8px;
                        font-weight:700;
                      "
                    >
                      {otp}
                    </div>

                    <p
                      style="
                        color:#64748b;
                        font-size:14px;
                        line-height:22px;
                      "
                    >
                      This verification code expires in
                      <strong>{minutes} minutes</strong>.
                    </p>

                    <p
                      style="
                        margin-top:24px;
                        color:#94a3b8;
                        font-size:12px;
                        line-height:20px;
                      "
                    >
                      If you did not create a Career
                      Intelligence account, you can safely
                      ignore this email.
                    </p>
                  </div>

                  <p
                    style="
                      text-align:center;
                      color:#94a3b8;
                      font-size:12px;
                      margin-top:20px;
                    "
                  >
                    Career Intelligence Platform
                  </p>
                </div>
              </body>
            </html>
            """,
            subtype="html",
        )

        return message
