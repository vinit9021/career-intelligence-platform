from collections.abc import Iterable

from app.parsers.base import (
    ResumeDocumentParser,
    ResumeExtension,
    UnsupportedResumeTypeError,
)
from app.parsers.docx import DocxResumeParser
from app.parsers.pdf import PdfResumeParser


class ResumeParserRegistry:
    def __init__(self, parsers: Iterable[ResumeDocumentParser]) -> None:
        self._parsers: dict[ResumeExtension, ResumeDocumentParser] = {
            parser.extension: parser for parser in parsers
        }

    def get(self, extension: str) -> ResumeDocumentParser:
        normalized = extension.lower().lstrip(".")

        if normalized == "pdf":
            key: ResumeExtension = "pdf"
        elif normalized == "docx":
            key = "docx"
        else:
            raise UnsupportedResumeTypeError(f"No resume parser is registered for '{extension}'.")

        try:
            return self._parsers[key]
        except KeyError as exc:
            raise UnsupportedResumeTypeError(
                f"No resume parser is registered for '{extension}'."
            ) from exc


def build_default_parser_registry() -> ResumeParserRegistry:
    return ResumeParserRegistry(
        parsers=(
            PdfResumeParser(),
            DocxResumeParser(),
        )
    )
