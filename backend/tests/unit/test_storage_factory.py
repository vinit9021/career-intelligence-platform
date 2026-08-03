from app.core.config import Settings
from app.storage import (
    LocalStorage,
    S3Storage,
    build_storage,
)


def build_settings(
    **overrides: object,
) -> Settings:
    data: dict[str, object] = {
        "app_env": "test",
        "postgres_host": "unused",
        "postgres_db": "unused",
        "postgres_user": "unused",
        "postgres_password": "unused",
        "jwt_access_secret": "a" * 64,
        "jwt_refresh_secret": "b" * 64,
    }

    data.update(overrides)

    return Settings.model_validate(data)


def test_local_storage_is_built() -> None:
    storage = build_storage(
        build_settings(
            storage_backend="local",
            local_storage_path=("test-storage"),
        )
    )

    assert isinstance(
        storage,
        LocalStorage,
    )


def test_s3_storage_is_built() -> None:
    storage = build_storage(
        build_settings(
            storage_backend="s3",
            aws_s3_bucket="resume-bucket",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
    )

    assert isinstance(
        storage,
        S3Storage,
    )
