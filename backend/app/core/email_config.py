from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from pydantic import (
    EmailStr,
    Field,
    SecretStr,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class SmtpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    smtp_host: str = Field(min_length=1)

    smtp_port: int = Field(
        gt=0,
        le=65535,
    )

    smtp_username: EmailStr

    smtp_app_password: SecretStr

    smtp_from_name: str = Field(
        default=("Career Intelligence"),
        min_length=1,
    )

    smtp_use_tls: bool = True

    smtp_timeout_seconds: int = Field(
        default=20,
        gt=0,
    )


@lru_cache
def get_smtp_settings() -> SmtpSettings:
    settings_factory = cast(
        Any,
        SmtpSettings,
    )

    return cast(
        SmtpSettings,
        settings_factory(),
    )
