import re
from io import BytesIO

import pypdf
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.parsers.base import (
    EncryptedResumeError,
    ExtractedDocument,
    ResumeExtension,
    ResumeParserError,
    normalize_extracted_text,
)


class PdfResumeParser:
    def __init__(
        self,
        *,
        minimum_total_characters: int = 80,
        minimum_characters_per_page: int = 40,
    ) -> None:
        self._minimum_total_characters = minimum_total_characters
        self._minimum_characters_per_page = minimum_characters_per_page

    @property
    def extension(self) -> ResumeExtension:
        return "pdf"

    @property
    def name(self) -> str:
        return "pypdf"

    @property
    def version(self) -> str:
        return pypdf.__version__

    def parse(self, data: bytes) -> ExtractedDocument:
        try:
            reader = PdfReader(BytesIO(data), strict=False)
        except (PdfReadError, ValueError) as exc:
            raise ResumeParserError("The PDF document could not be opened.") from exc

        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
            except (PdfReadError, ValueError) as exc:
                raise EncryptedResumeError(
                    "Password-protected PDF resumes are not supported."
                ) from exc

            if not decrypted:
                raise EncryptedResumeError("Password-protected PDF resumes are not supported.")

        page_count = len(reader.pages)

        if page_count == 0:
            raise ResumeParserError("The PDF document does not contain any pages.")

        page_texts: list[str] = []
        warnings: list[str] = []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except (PdfReadError, KeyError, TypeError, ValueError) as exc:
                warnings.append(
                    f"Page {page_number} could not be extracted ({type(exc).__name__})."
                )
                text = ""

            normalized = normalize_extracted_text(text)

            if normalized:
                page_texts.append(normalized)

        raw_text = "\n\n".join(page_texts)
        meaningful_characters = len(re.sub(r"\s+", "", raw_text))
        ocr_threshold = max(
            self._minimum_total_characters,
            page_count * self._minimum_characters_per_page,
        )
        requires_ocr = meaningful_characters < ocr_threshold

        if requires_ocr:
            warnings.append(
                "The PDF contains too little extractable text and should be sent to an OCR worker."
            )

        return ExtractedDocument(
            raw_text=raw_text,
            page_count=page_count,
            requires_ocr=requires_ocr,
            warnings=tuple(warnings),
        )
