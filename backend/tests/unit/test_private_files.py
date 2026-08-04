import pytest

from app.core.private_files import build_private_file_headers


def test_private_file_headers_are_hardened() -> None:
    headers = build_private_file_headers(
        filename="Resume Final.pdf",
        sha256="A" * 64,
        size_bytes=128,
    )

    assert headers == {
        "Content-Disposition": ("attachment; filename*=UTF-8''Resume%20Final.pdf"),
        "Content-Length": "128",
        "Cache-Control": "private, no-store",
        "Pragma": "no-cache",
        "X-Content-SHA256": "a" * 64,
        "X-Content-Type-Options": "nosniff",
    }


def test_private_file_headers_support_inline_and_unicode() -> None:
    headers = build_private_file_headers(
        filename=" résumé.pdf ",
        sha256="b" * 64,
        size_bytes=0,
        disposition="inline",
    )

    assert headers["Content-Disposition"] == ("inline; filename*=UTF-8''r%C3%A9sum%C3%A9.pdf")
    assert headers["Content-Length"] == "0"


def test_blank_filename_uses_safe_fallback() -> None:
    headers = build_private_file_headers(
        filename="   ",
        sha256="c" * 64,
        size_bytes=1,
    )

    assert headers["Content-Disposition"] == ("attachment; filename*=UTF-8''resume")


@pytest.mark.parametrize(
    "checksum",
    [
        "",
        "a" * 63,
        "a" * 65,
        "g" * 64,
    ],
)
def test_invalid_checksum_is_rejected(checksum: str) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        build_private_file_headers(
            filename="resume.pdf",
            sha256=checksum,
            size_bytes=1,
        )


def test_negative_file_size_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        build_private_file_headers(
            filename="resume.pdf",
            sha256="d" * 64,
            size_bytes=-1,
        )
