from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.services.resumes import (
    InvalidResumeError,
    ResumeTooLargeError,
    validate_resume_upload,
)


def build_docx() -> bytes:
    buffer = BytesIO()

    with ZipFile(
        buffer,
        mode="w",
        compression=ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<Types />",
        )
        archive.writestr(
            "word/document.xml",
            "<document />",
        )

    return buffer.getvalue()


def test_valid_pdf_is_normalized() -> None:
    result = validate_resume_upload(
        filename=(r"C:\fakepath\Resume.PDF"),
        content_type="application/pdf",
        data=b"%PDF-1.7\nresume",
        max_size_bytes=1024,
    )

    assert result.original_filename == "Resume.PDF"
    assert result.extension == "pdf"
    assert result.content_type == "application/pdf"
    assert len(result.sha256) == 64


def test_valid_docx_is_accepted() -> None:
    result = validate_resume_upload(
        filename="resume.docx",
        content_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        data=build_docx(),
        max_size_bytes=10000,
    )

    assert result.extension == "docx"


@pytest.mark.parametrize(
    ("filename", "content_type", "data"),
    [
        (
            "resume.txt",
            "text/plain",
            b"resume",
        ),
        (
            "resume.pdf",
            "application/pdf",
            b"not-a-pdf",
        ),
        (
            "resume.docx",
            ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            b"not-a-docx",
        ),
        (
            "resume.pdf",
            "text/plain",
            b"%PDF-1.7\nresume",
        ),
    ],
)
def test_invalid_resume_is_rejected(
    filename: str,
    content_type: str,
    data: bytes,
) -> None:
    with pytest.raises(InvalidResumeError):
        validate_resume_upload(
            filename=filename,
            content_type=content_type,
            data=data,
            max_size_bytes=10000,
        )


def test_empty_resume_is_rejected() -> None:
    with pytest.raises(InvalidResumeError):
        validate_resume_upload(
            filename="resume.pdf",
            content_type="application/pdf",
            data=b"",
            max_size_bytes=100,
        )


def test_oversized_resume_is_rejected() -> None:
    with pytest.raises(ResumeTooLargeError):
        validate_resume_upload(
            filename="resume.pdf",
            content_type="application/pdf",
            data=b"%PDF-" + b"x" * 20,
            max_size_bytes=10,
        )


def test_docx_missing_required_member_is_rejected() -> None:
    buffer = BytesIO()

    with ZipFile(
        buffer,
        mode="w",
    ) as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<Types />",
        )

    with pytest.raises(InvalidResumeError):
        validate_resume_upload(
            filename="resume.docx",
            content_type=None,
            data=buffer.getvalue(),
            max_size_bytes=10000,
        )
