import pytest
from pydantic import SecretStr

from app.parsers.base import UnsupportedResumeTypeError
from app.parsers.registry import ResumeParserRegistry, build_default_parser_registry
from app.storage.base import InvalidStorageKeyError, normalize_storage_key
from app.storage.factory import optional_secret_value, optional_text


@pytest.mark.parametrize(
    "key",
    [
        "",
        "   ",
        r"resumes\user\resume.pdf",
        "/resumes/user/resume.pdf",
    ],
)
def test_invalid_storage_keys_are_rejected(
    key: str,
) -> None:
    with pytest.raises(InvalidStorageKeyError):
        normalize_storage_key(key)


def test_valid_storage_key_is_normalized() -> None:
    assert normalize_storage_key("resumes/user/resume.pdf") == "resumes/user/resume.pdf"


def test_default_registry_resolves_pdf_and_docx() -> None:
    registry = build_default_parser_registry()

    assert registry.get(".PDF").extension == "pdf"
    assert registry.get("DOCX").extension == "docx"


def test_registry_rejects_unsupported_extension() -> None:
    registry = build_default_parser_registry()

    with pytest.raises(UnsupportedResumeTypeError):
        registry.get("txt")


def test_registry_rejects_missing_registered_parser() -> None:
    registry = ResumeParserRegistry(parsers=())

    with pytest.raises(UnsupportedResumeTypeError):
        registry.get("pdf")


def test_optional_storage_values_are_normalized() -> None:
    assert optional_secret_value(None) is None
    assert optional_secret_value(SecretStr("   ")) is None
    assert optional_secret_value(SecretStr("secret")) == "secret"

    assert optional_text(None) is None
    assert optional_text("   ") is None
    assert optional_text(" value ") == "value"
