from pathlib import Path

import boto3
import pytest
from botocore.stub import Stubber
from mypy_boto3_s3.client import S3Client

from app.storage import (
    InvalidStorageKeyError,
    LocalStorage,
    S3Storage,
    StorageOperationError,
)


@pytest.mark.asyncio
async def test_local_storage_lifecycle(
    tmp_path: Path,
) -> None:
    storage = LocalStorage(tmp_path / "storage")

    result = await storage.save(
        key="resumes/user/resume.pdf",
        data=b"resume-data",
        content_type="application/pdf",
        checksum_sha256="a" * 64,
    )

    stored_path = storage.root / "resumes" / "user" / "resume.pdf"

    assert stored_path.read_bytes() == b"resume-data"
    assert result.key == "resumes/user/resume.pdf"
    assert result.etag == "a" * 64
    assert result.size_bytes == 11

    await storage.delete(key=result.key)

    assert stored_path.exists() is False


@pytest.mark.asyncio
async def test_invalid_local_key_is_rejected(
    tmp_path: Path,
) -> None:
    storage = LocalStorage(tmp_path / "storage")

    with pytest.raises(InvalidStorageKeyError):
        await storage.save(
            key="../resume.pdf",
            data=b"resume",
            content_type="application/pdf",
            checksum_sha256="a" * 64,
        )


def build_s3_client() -> S3Client:
    return boto3.client(
        "s3",
        region_name="ap-south-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@pytest.mark.asyncio
async def test_s3_storage_lifecycle() -> None:
    client = build_s3_client()

    expected_put = {
        "Bucket": "resume-bucket",
        "Key": "resumes/user/resume.pdf",
        "Body": b"resume-data",
        "ContentType": "application/pdf",
        "Metadata": {
            "sha256": "b" * 64,
        },
        "ServerSideEncryption": "AES256",
    }

    expected_delete = {
        "Bucket": "resume-bucket",
        "Key": "resumes/user/resume.pdf",
    }

    with Stubber(client) as stubber:
        stubber.add_response(
            "put_object",
            {
                "ETag": '"etag-value"',
            },
            expected_put,
        )

        stubber.add_response(
            "delete_object",
            {},
            expected_delete,
        )

        storage = S3Storage(
            bucket="resume-bucket",
            region="ap-south-1",
            client=client,
        )

        result = await storage.save(
            key="resumes/user/resume.pdf",
            data=b"resume-data",
            content_type="application/pdf",
            checksum_sha256="b" * 64,
        )

        assert result.etag == "etag-value"

        await storage.delete(key=result.key)


@pytest.mark.asyncio
async def test_s3_kms_encryption() -> None:
    client = build_s3_client()

    with Stubber(client) as stubber:
        stubber.add_response(
            "put_object",
            {
                "ETag": '"kms-etag"',
            },
            {
                "Bucket": "resume-bucket",
                "Key": "resumes/user/resume.pdf",
                "Body": b"resume-data",
                "ContentType": "application/pdf",
                "Metadata": {
                    "sha256": "c" * 64,
                },
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": "kms-key-id",
            },
        )

        storage = S3Storage(
            bucket="resume-bucket",
            region="ap-south-1",
            kms_key_id="kms-key-id",
            client=client,
        )

        result = await storage.save(
            key="resumes/user/resume.pdf",
            data=b"resume-data",
            content_type="application/pdf",
            checksum_sha256="c" * 64,
        )

        assert result.etag == "kms-etag"


@pytest.mark.asyncio
async def test_s3_error_is_wrapped() -> None:
    client = build_s3_client()

    with Stubber(client) as stubber:
        stubber.add_client_error(
            "put_object",
            service_error_code="AccessDenied",
            service_message="Denied",
            http_status_code=403,
        )

        storage = S3Storage(
            bucket="resume-bucket",
            region="ap-south-1",
            client=client,
        )

        with pytest.raises(StorageOperationError):
            await storage.save(
                key="resumes/user/resume.pdf",
                data=b"resume-data",
                content_type="application/pdf",
                checksum_sha256="d" * 64,
            )
