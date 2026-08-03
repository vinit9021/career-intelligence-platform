from collections.abc import Sequence
from typing import Any

import pytest
from pytest import MonkeyPatch

from app.parsers import EncryptedResumeError
from app.parsers.pdf import PdfResumeParser


class FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class FakeReader:
    def __init__(
        self,
        pages: Sequence[FakePage],
        *,
        encrypted: bool = False,
        decrypt_result: int = 1,
    ) -> None:
        self.pages = list(pages)
        self.is_encrypted = encrypted
        self._decrypt_result = decrypt_result

    def decrypt(self, _password: str) -> int:
        return self._decrypt_result


def install_reader(
    monkeypatch: MonkeyPatch,
    reader: FakeReader,
) -> None:
    def build_reader(*_args: Any, **_kwargs: Any) -> FakeReader:
        return reader

    monkeypatch.setattr("app.parsers.pdf.PdfReader", build_reader)


def test_pdf_parser_preserves_page_order(monkeypatch: MonkeyPatch) -> None:
    install_reader(
        monkeypatch,
        FakeReader(
            [
                FakePage("Summary\nBackend engineer with Python and FastAPI."),
                FakePage("Skills\nPython, SQL, Docker, PostgreSQL"),
            ]
        ),
    )
    parser = PdfResumeParser(
        minimum_total_characters=10,
        minimum_characters_per_page=5,
    )

    result = parser.parse(b"pdf-data")

    assert result.page_count == 2
    assert result.raw_text.startswith("Summary")
    assert result.raw_text.endswith("PostgreSQL")
    assert result.requires_ocr is False


def test_pdf_parser_marks_low_text_for_ocr(monkeypatch: MonkeyPatch) -> None:
    install_reader(monkeypatch, FakeReader([FakePage("")]))

    result = PdfResumeParser().parse(b"pdf-data")

    assert result.requires_ocr is True
    assert "OCR worker" in result.warnings[0]


def test_encrypted_pdf_is_rejected(monkeypatch: MonkeyPatch) -> None:
    install_reader(
        monkeypatch,
        FakeReader([FakePage("text")], encrypted=True, decrypt_result=0),
    )

    with pytest.raises(EncryptedResumeError):
        PdfResumeParser().parse(b"encrypted-pdf")
