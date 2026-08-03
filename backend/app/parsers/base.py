from dataclasses import dataclass
from typing import Literal, Protocol

ResumeExtension = Literal["pdf", "docx"]


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    raw_text: str
    page_count: int | None
    requires_ocr: bool
    warnings: tuple[str, ...]


class ResumeParserError(RuntimeError):
    pass


class EncryptedResumeError(ResumeParserError):
    pass


class UnsupportedResumeTypeError(ResumeParserError):
    pass


def normalize_extracted_text(value: str) -> str:
    normalized_lines: list[str] = []

    for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        normalized = " ".join(line.split())

        if normalized:
            normalized_lines.append(normalized)

    return "\n".join(normalized_lines)


class ResumeDocumentParser(Protocol):
    @property
    def extension(self) -> ResumeExtension: ...

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def parse(self, data: bytes) -> ExtractedDocument: ...
