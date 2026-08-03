import re
from io import BytesIO
from zipfile import BadZipFile

import docx
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.parsers.base import (
    ExtractedDocument,
    ResumeExtension,
    ResumeParserError,
    normalize_extracted_text,
)


class DocxResumeParser:
    def __init__(self, *, minimum_total_characters: int = 20) -> None:
        self._minimum_total_characters = minimum_total_characters

    @property
    def extension(self) -> ResumeExtension:
        return "docx"

    @property
    def name(self) -> str:
        return "python-docx"

    @property
    def version(self) -> str:
        return docx.__version__

    def parse(self, data: bytes) -> ExtractedDocument:
        try:
            document = docx.Document(BytesIO(data))
        except (PackageNotFoundError, BadZipFile, KeyError, ValueError) as exc:
            raise ResumeParserError("The DOCX document could not be opened.") from exc

        blocks: list[str] = []

        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                text = normalize_extracted_text(block.text)

                if text:
                    blocks.append(text)

            elif isinstance(block, Table):
                for row in block.rows:
                    cell_values = [
                        normalize_extracted_text(cell.text).replace("\n", " ") for cell in row.cells
                    ]
                    row_text = " | ".join(value for value in cell_values if value)

                    if row_text:
                        blocks.append(row_text)

        raw_text = "\n".join(blocks)
        meaningful_characters = len(re.sub(r"\s+", "", raw_text))
        requires_ocr = meaningful_characters < self._minimum_total_characters
        warnings: list[str] = []

        if requires_ocr:
            warnings.append(
                "The DOCX file contains too little extractable text and may contain "
                "image-only content."
            )

        return ExtractedDocument(
            raw_text=raw_text,
            page_count=None,
            requires_ocr=requires_ocr,
            warnings=tuple(warnings),
        )
