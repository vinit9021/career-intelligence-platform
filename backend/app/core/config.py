from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Career Intelligence Platform API"
    app_env: Literal[
        "development",
        "test",
        "staging",
        "production",
    ] = "development"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    log_level: str = "INFO"

    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr

    jwt_access_secret: SecretStr
    jwt_refresh_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "career-intelligence-platform"
    jwt_audience: str = "career-intelligence-platform-api"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    storage_backend: Literal[
        "local",
        "s3",
    ] = "local"

    local_storage_path: str = "storage"

    resume_max_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
    )

    aws_region: str = "ap-south-1"
    aws_s3_bucket: str = ""
    aws_s3_endpoint_url: str | None = None
    aws_s3_kms_key_id: str | None = None

    aws_access_key_id: SecretStr | None = None
    aws_secret_access_key: SecretStr | None = None
    aws_session_token: SecretStr | None = None

    @model_validator(mode="after")
    def validate_storage_configuration(
        self,
    ) -> Self:
        if self.storage_backend == "s3" and not self.aws_s3_bucket.strip():
            raise ValueError("AWS_S3_BUCKET is required when STORAGE_BACKEND is s3.")

        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=(self.postgres_password.get_secret_value()),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def resume_max_size_bytes(self) -> int:
        return self.resume_max_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
