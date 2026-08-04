from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    JobSeniorityLevel,
    ParsedJobDescription,
)

MAX_JOB_DESCRIPTION_CHARS = 60_000
PARSER_NAME = "deterministic_job_description_parser"
PARSER_VERSION = "1.0.0"


class JobDescriptionParserError(ValueError):
    pass


class EmptyJobDescriptionError(JobDescriptionParserError):
    pass


class JobDescriptionTooLargeError(JobDescriptionParserError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedSections:
    preamble: list[str]
    sections: dict[str, list[str]]


SECTION_ALIASES: dict[str, set[str]] = {
    "required_skills": {
        "required skills",
        "must have",
        "must-have skills",
        "core skills",
        "technical requirements",
    },
    "preferred_skills": {
        "preferred skills",
        "nice to have",
        "nice-to-have",
        "preferred qualifications",
        "good to have",
    },
    "responsibilities": {
        "responsibilities",
        "key responsibilities",
        "what you will do",
        "what you'll do",
        "role responsibilities",
        "duties",
    },
    "qualifications": {
        "qualifications",
        "requirements",
        "minimum qualifications",
        "what you bring",
        "who you are",
        "candidate requirements",
    },
    "education": {
        "education",
        "education requirements",
        "academic qualifications",
    },
    "experience": {
        "experience",
        "experience requirements",
        "professional experience",
    },
}

TECHNOLOGY_TERMS: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "Java": ("java",),
    "C++": ("c++",),
    "C#": ("c#", "c sharp"),
    "JavaScript": ("javascript",),
    "TypeScript": ("typescript",),
    "SQL": ("sql",),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "React": ("react", "react.js", "reactjs"),
    "Next.js": ("next.js", "nextjs"),
    "Node.js": ("node.js", "nodejs"),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "MongoDB": ("mongodb",),
    "Redis": ("redis",),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "GCP": ("gcp", "google cloud platform"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Git": ("git",),
    "Linux": ("linux",),
    "REST APIs": ("rest api", "restful api", "rest apis"),
    "GraphQL": ("graphql",),
    "Kafka": ("kafka", "apache kafka"),
    "Spark": ("spark", "apache spark"),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "LangChain": ("langchain",),
    "LangGraph": ("langgraph",),
    "FAISS": ("faiss",),
    "Power BI": ("power bi",),
    "Tableau": ("tableau",),
    "Terraform": ("terraform",),
    "Jenkins": ("jenkins",),
}

SKILL_TERMS: dict[str, tuple[str, ...]] = {
    "Machine Learning": (
        "machine learning",
        "ml",
    ),
    "Deep Learning": ("deep learning",),
    "Natural Language Processing": (
        "natural language processing",
        "nlp",
    ),
    "Large Language Models": (
        "large language models",
        "large language model",
        "llms",
        "llm",
    ),
    "Data Structures": ("data structures",),
    "Algorithms": ("algorithms",),
    "System Design": ("system design",),
    "Microservices": ("microservices",),
    "Cloud Computing": ("cloud computing",),
    "Data Analysis": ("data analysis", "data analytics"),
    "Problem Solving": ("problem solving",),
    "Communication": (
        "communication skills",
        "communication",
    ),
    "Leadership": ("leadership",),
    "Stakeholder Management": ("stakeholder management",),
    "Agile": ("agile", "scrum"),
    "CI/CD": ("ci/cd", "continuous integration"),
}

EDUCATION_TERMS = (
    "bachelor",
    "b.tech",
    "btech",
    "master",
    "m.tech",
    "mtech",
    "phd",
    "doctorate",
    "degree",
    "diploma",
)

GENERIC_TITLE_LINES = {
    "job description",
    "about the role",
    "about us",
    "overview",
    "position overview",
}

BULLET_PATTERN = re.compile(r"^(?:[-*•▪◦‣]+|\d+[.)])\s*")


def normalize_job_description_text(
    text: str,
    *,
    max_chars: int = MAX_JOB_DESCRIPTION_CHARS,
) -> str:
    if len(text) > max_chars:
        raise JobDescriptionTooLargeError("The job description exceeds the maximum allowed length.")

    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned = "".join(
        character
        for character in normalized_newlines
        if character in {"\n", "\t"} or ord(character) >= 32
    )

    lines: list[str] = []

    for raw_line in cleaned.split("\n"):
        line = re.sub(
            r"[ \t]+",
            " ",
            raw_line,
        ).strip()

        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")

    normalized = "\n".join(lines).strip()

    if not normalized:
        raise EmptyJobDescriptionError("The job description must not be empty.")

    return normalized


def _normalize_heading(line: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        line.strip().lower().rstrip(":-"),
    )


def _section_name(line: str) -> str | None:
    heading = _normalize_heading(line)

    for section_name, aliases in SECTION_ALIASES.items():
        if heading in aliases:
            return section_name

    return None


def _clean_item(line: str) -> str:
    return BULLET_PATTERN.sub("", line).strip()


def _unique(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in items:
        normalized = item.strip()
        key = normalized.casefold()

        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)

    return result


def _parse_sections(
    normalized_text: str,
) -> ParsedSections:
    preamble: list[str] = []
    sections: dict[str, list[str]] = {name: [] for name in SECTION_ALIASES}
    current_section: str | None = None

    for line in normalized_text.splitlines():
        if not line:
            continue

        detected_section = _section_name(line)

        if detected_section is not None:
            current_section = detected_section
            continue

        item = _clean_item(line)

        if not item:
            continue

        if current_section is None:
            preamble.append(item)
        else:
            sections[current_section].append(item)

    return ParsedSections(
        preamble=preamble,
        sections=sections,
    )


def _extract_labeled_value(
    text: str,
    labels: tuple[str, ...],
) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(rf"(?im)^\s*(?:{label_pattern})\s*[:\-]\s*(.+?)\s*$")
    match = pattern.search(text)

    if match is None:
        return None

    value = match.group(1).strip()
    return value or None


def _extract_job_title(
    normalized_text: str,
    preamble: list[str],
) -> str | None:
    labeled = _extract_labeled_value(
        normalized_text,
        (
            "job title",
            "position",
            "role",
            "position title",
        ),
    )

    if labeled is not None:
        return labeled

    for line in preamble[:5]:
        lowered = line.casefold()

        if (
            lowered not in GENERIC_TITLE_LINES
            and len(line) <= 120
            and not lowered.startswith("company:")
            and not lowered.startswith("location:")
        ):
            return line

    return None


def _extract_company_name(
    normalized_text: str,
    preamble: list[str],
) -> str | None:
    labeled = _extract_labeled_value(
        normalized_text,
        (
            "company",
            "company name",
            "organization",
            "organisation",
        ),
    )

    if labeled is not None:
        return labeled

    about_pattern = re.compile(r"(?i)^about\s+(.+)$")

    recruiting_patterns = (
        re.compile(
            r"(?i)^at\s+(?P<company>.+?)[,;]\s+"
            r"we\s+(?:are\s+)?(?:currently\s+)?"
            r"(?:looking|hiring|seeking|recruiting)\b"
        ),
        re.compile(
            r"(?i)^(?:we\s+)?(?P<company>.+?)\s+"
            r"(?:is|are)\s+(?:currently\s+)?"
            r"(?:looking|hiring|seeking|recruiting)\b"
        ),
    )

    invalid_candidates = {
        "we",
        "company",
        "the company",
        "our company",
        "the team",
        "our team",
    }

    for line in preamble:
        about_match = about_pattern.match(line)

        if about_match is not None:
            candidate = about_match.group(1).strip()

            if candidate.casefold() not in {
                "the role",
                "the position",
                "us",
            }:
                return candidate

        for pattern in recruiting_patterns:
            match = pattern.match(line)

            if match is None:
                continue

            candidate = match.group("company").strip(" ,:;-")

            if (
                candidate
                and candidate.casefold() not in invalid_candidates
                and len(candidate) <= 120
                and len(candidate.split()) <= 10
            ):
                return candidate

    return None


def _contains_alias(
    text: str,
    alias: str,
) -> bool:
    escaped = re.escape(alias)
    pattern = re.compile(
        rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    return pattern.search(text) is not None


def _extract_terms(
    text: str,
    vocabulary: dict[str, tuple[str, ...]],
) -> list[str]:
    matches: list[str] = []

    for canonical, aliases in vocabulary.items():
        if any(_contains_alias(text, alias) for alias in aliases):
            matches.append(canonical)

    return matches


def _extract_required_skills(
    sections: ParsedSections,
    normalized_text: str,
) -> list[str]:
    required_text = "\n".join(
        sections.sections["required_skills"] + sections.sections["qualifications"]
    )

    if not required_text:
        required_text = normalized_text

    return _unique(
        _extract_terms(
            required_text,
            TECHNOLOGY_TERMS,
        )
        + _extract_terms(
            required_text,
            SKILL_TERMS,
        )
    )


def _extract_preferred_skills(
    sections: ParsedSections,
) -> list[str]:
    preferred_text = "\n".join(sections.sections["preferred_skills"])

    return _unique(
        _extract_terms(
            preferred_text,
            TECHNOLOGY_TERMS,
        )
        + _extract_terms(
            preferred_text,
            SKILL_TERMS,
        )
    )


def _extract_experience(
    normalized_text: str,
    sections: ParsedSections,
) -> JobExperienceRequirement:
    candidates = sections.sections["experience"]
    search_text = "\n".join(candidates)

    if not search_text:
        relevant_lines = [
            line for line in normalized_text.splitlines() if "experience" in line.casefold()
        ]
        search_text = "\n".join(relevant_lines)

    range_pattern = re.compile(
        r"(?i)\b(\d{1,2})\s*(?:-|–|to)\s*"
        r"(\d{1,2})\s*(?:\+\s*)?years?\b"
    )
    range_match = range_pattern.search(search_text)

    if range_match is not None:
        minimum = int(range_match.group(1))
        maximum = int(range_match.group(2))

        if maximum < minimum:
            minimum, maximum = maximum, minimum

        return JobExperienceRequirement(
            min_years=minimum,
            max_years=maximum,
            statement=_matching_line(
                search_text,
                range_match.group(0),
            ),
        )

    minimum_pattern = re.compile(
        r"(?i)\b(?:minimum\s+of\s+)?"
        r"(\d{1,2})\s*(?:\+|plus)?\s*years?\b"
    )
    minimum_match = minimum_pattern.search(search_text)

    if minimum_match is None:
        return JobExperienceRequirement()

    minimum = int(minimum_match.group(1))

    return JobExperienceRequirement(
        min_years=minimum,
        max_years=None,
        statement=_matching_line(
            search_text,
            minimum_match.group(0),
        ),
    )


def _matching_line(
    text: str,
    fragment: str,
) -> str | None:
    fragment_key = fragment.casefold()

    for line in text.splitlines():
        if fragment_key in line.casefold():
            return line.strip()

    return None


def _extract_education(
    normalized_text: str,
    sections: ParsedSections,
) -> list[str]:
    education_items = list(sections.sections["education"])

    for line in normalized_text.splitlines():
        lowered = line.casefold()

        if any(term in lowered for term in EDUCATION_TERMS):
            education_items.append(_clean_item(line))

    return _unique(education_items)


def _extract_seniority(
    job_title: str | None,
    normalized_text: str,
) -> JobSeniorityLevel:
    title = (job_title or "").casefold()
    combined = f"{title}\n{normalized_text.casefold()}"

    ordered_patterns: tuple[
        tuple[JobSeniorityLevel, tuple[str, ...]],
        ...,
    ] = (
        (
            "executive",
            ("chief ", "vice president", "vp "),
        ),
        (
            "director",
            ("director", "head of"),
        ),
        (
            "manager",
            ("manager", "management role"),
        ),
        (
            "lead",
            ("tech lead", "team lead", "lead engineer"),
        ),
        (
            "senior",
            ("senior", "sr.", "sr ", "staff engineer"),
        ),
        (
            "intern",
            ("intern", "internship"),
        ),
        (
            "entry",
            (
                "entry level",
                "entry-level",
                "junior",
                "graduate role",
                "fresher",
            ),
        ),
        (
            "mid",
            ("mid level", "mid-level", "associate"),
        ),
    )

    for level, markers in ordered_patterns:
        if any(marker in combined for marker in markers):
            return level

    return "unspecified"


def parse_job_description(
    text: str,
    *,
    max_chars: int = MAX_JOB_DESCRIPTION_CHARS,
) -> ParsedJobDescription:
    normalized_text = normalize_job_description_text(
        text,
        max_chars=max_chars,
    )
    sections = _parse_sections(normalized_text)
    job_title = _extract_job_title(
        normalized_text,
        sections.preamble,
    )
    company_name = _extract_company_name(
        normalized_text,
        sections.preamble,
    )
    required_skills = _extract_required_skills(
        sections,
        normalized_text,
    )
    preferred_skills = _extract_preferred_skills(sections)
    technologies = _extract_terms(
        normalized_text,
        TECHNOLOGY_TERMS,
    )
    responsibilities = _unique(sections.sections["responsibilities"])
    qualifications = _unique(sections.sections["qualifications"])
    experience = _extract_experience(
        normalized_text,
        sections,
    )
    education_requirements = _extract_education(
        normalized_text,
        sections,
    )
    seniority_level = _extract_seniority(
        job_title,
        normalized_text,
    )

    ats_keywords = _unique(
        technologies
        + _extract_terms(
            normalized_text,
            SKILL_TERMS,
        )
        + required_skills
        + preferred_skills
    )

    warnings: list[str] = []

    if job_title is None:
        warnings.append("Job title could not be identified.")

    if company_name is None:
        warnings.append("Company name could not be identified.")

    if not responsibilities:
        warnings.append("Responsibilities section was not found.")

    if not qualifications:
        warnings.append("Qualifications section was not found.")

    return ParsedJobDescription(
        job_title=job_title,
        company_name=company_name,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        technologies=technologies,
        responsibilities=responsibilities,
        qualifications=qualifications,
        experience=experience,
        education_requirements=(education_requirements),
        seniority_level=seniority_level,
        ats_keywords=ats_keywords,
        normalized_text=normalized_text,
        metadata=JobDescriptionParserMetadata(
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
            character_count=len(normalized_text),
            warnings=warnings,
        ),
    )


class JobDescriptionParser:
    def __init__(
        self,
        *,
        max_chars: int = MAX_JOB_DESCRIPTION_CHARS,
    ) -> None:
        self._max_chars = max_chars

    def parse(
        self,
        text: str,
    ) -> ParsedJobDescription:
        return parse_job_description(
            text,
            max_chars=self._max_chars,
        )
