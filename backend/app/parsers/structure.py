import re
from collections.abc import Iterable
from typing import Literal

from app.parsers.base import ExtractedDocument, ResumeExtension
from app.schemas.resume_parsing import (
    ResumeContactInformation,
    ResumeParseMetadata,
    ResumeStructuredContent,
)

SectionName = Literal[
    "summary",
    "skills",
    "education",
    "experience",
    "projects",
    "certifications",
]

SECTION_ALIASES: dict[str, SectionName] = {
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "professional profile": "summary",
    "objective": "summary",
    "career objective": "summary",
    "skills": "skills",
    "technical skills": "skills",
    "core skills": "skills",
    "technologies": "skills",
    "education": "education",
    "academic background": "education",
    "academics": "education",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "internships": "experience",
    "projects": "projects",
    "academic projects": "projects",
    "personal projects": "projects",
    "certifications": "certifications",
    "certificates": "certifications",
    "licenses and certifications": "certifications",
}

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d().\- ]{7,}\d)(?!\w)")
URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s,;]+", re.IGNORECASE)


def _normalize_heading(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9 ]+", " ", value.lower())
    return " ".join(normalized.split())


def _match_heading(line: str) -> tuple[SectionName | None, str | None]:
    stripped = line.strip().lstrip("•*-–— ")

    if ":" in stripped:
        prefix, remainder = stripped.split(":", 1)
        section = SECTION_ALIASES.get(_normalize_heading(prefix))

        if section is not None:
            normalized_remainder = remainder.strip()
            return section, normalized_remainder or None

    section = SECTION_ALIASES.get(_normalize_heading(stripped))
    return section, None


def _deduplicate(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = value.strip().strip("•*-–— ")
        key = normalized.casefold()

        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)

    return result


def _split_sections(raw_text: str) -> dict[SectionName, list[str]]:
    sections: dict[SectionName, list[str]] = {
        "summary": [],
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
    }
    current_section: SectionName | None = None

    for line in raw_text.splitlines():
        normalized_line = line.strip()

        if not normalized_line:
            continue

        matched_section, inline_value = _match_heading(normalized_line)

        if matched_section is not None:
            current_section = matched_section

            if inline_value:
                sections[current_section].append(inline_value)

            continue

        if current_section is not None:
            sections[current_section].append(normalized_line)

    return sections


def _extract_phone(raw_text: str) -> str | None:
    for candidate in PHONE_PATTERN.findall(raw_text):
        digit_count = sum(character.isdigit() for character in candidate)

        if 10 <= digit_count <= 15:
            return " ".join(candidate.split())

    return None


def _extract_contact_information(raw_text: str) -> ResumeContactInformation:
    email_match = EMAIL_PATTERN.search(raw_text)
    urls = _deduplicate(URL_PATTERN.findall(raw_text))
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    for url in urls:
        lowered = url.lower()

        if "linkedin.com" in lowered and linkedin_url is None:
            linkedin_url = url
        elif "github.com" in lowered and github_url is None:
            github_url = url
        elif portfolio_url is None:
            portfolio_url = url

    return ResumeContactInformation(
        email=email_match.group(0) if email_match else None,
        phone=_extract_phone(raw_text),
        linkedin_url=linkedin_url,
        github_url=github_url,
        portfolio_url=portfolio_url,
    )


def _extract_skills(lines: Iterable[str]) -> list[str]:
    values: list[str] = []

    for line in lines:
        values.extend(re.split(r"[,;|•·]", line))

    return [value for value in _deduplicate(values) if len(value) <= 80]


def build_structured_resume(
    *,
    extracted: ExtractedDocument,
    source_type: ResumeExtension,
    parser_name: str,
    parser_version: str,
) -> tuple[ResumeStructuredContent, ResumeParseMetadata]:
    sections = _split_sections(extracted.raw_text)
    warnings = list(extracted.warnings)

    required_sections: tuple[SectionName, ...] = (
        "skills",
        "education",
        "experience",
        "projects",
    )

    for section_name in required_sections:
        if not sections[section_name]:
            warnings.append(f"No '{section_name}' section was detected.")

    summary_lines = _deduplicate(sections["summary"])
    content = ResumeStructuredContent(
        contact=_extract_contact_information(extracted.raw_text),
        summary=" ".join(summary_lines) if summary_lines else None,
        skills=_extract_skills(sections["skills"]),
        education=_deduplicate(sections["education"]),
        experience=_deduplicate(sections["experience"]),
        projects=_deduplicate(sections["projects"]),
        certifications=_deduplicate(sections["certifications"]),
    )
    metadata = ResumeParseMetadata(
        source_type=source_type,
        parser_name=parser_name,
        parser_version=parser_version,
        page_count=extracted.page_count,
        character_count=len(extracted.raw_text),
        requires_ocr=extracted.requires_ocr,
        warnings=_deduplicate(warnings),
    )

    return content, metadata
