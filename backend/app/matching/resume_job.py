from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.schemas.job_description_parser import ParsedJobDescription
from app.schemas.resume_matching import (
    EducationComparison,
    ExperienceComparison,
    MatchCategoryScore,
    MatchingCategory,
    RequirementEvidence,
    RequirementStatus,
    ResponsibilityMatch,
    ResponsibilityStatus,
    ResumeJobMatchRequest,
    ResumeJobMatchResult,
    ResumeMatchingMetadata,
)
from app.schemas.resume_parsing import ResumeStructuredContent

ENGINE_NAME = "deterministic_resume_job_matcher"
ENGINE_VERSION = "1.0.0"

CATEGORY_WEIGHTS: dict[MatchingCategory, float] = {
    "required_skills": 0.30,
    "preferred_skills": 0.10,
    "technologies": 0.15,
    "ats_keywords": 0.15,
    "experience": 0.10,
    "education": 0.05,
    "responsibilities": 0.15,
}

ALIASES: dict[str, tuple[str, ...]] = {
    "amazon web services": (
        "amazon web services",
        "aws",
    ),
    "continuous integration continuous delivery": (
        "ci cd",
        "ci/cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
    ),
    "c sharp": (
        "c sharp",
        "c#",
    ),
    "cplusplus": (
        "cplusplus",
        "c++",
        "cpp",
    ),
    "google cloud platform": (
        "google cloud platform",
        "gcp",
    ),
    "javascript": (
        "javascript",
        "java script",
        "js",
    ),
    "kubernetes": (
        "kubernetes",
        "k8s",
    ),
    "machine learning": (
        "machine learning",
        "ml",
    ),
    "natural language processing": (
        "natural language processing",
        "nlp",
    ),
    "node js": (
        "node js",
        "node.js",
        "nodejs",
    ),
    "next js": (
        "next js",
        "next.js",
        "nextjs",
    ),
    "postgresql": (
        "postgresql",
        "postgres",
        "postgre sql",
    ),
    "react": (
        "react",
        "react js",
        "react.js",
        "reactjs",
    ),
    "rest api": (
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
    ),
    "structured query language": (
        "structured query language",
        "sql",
    ),
    "typescript": (
        "typescript",
        "type script",
        "ts",
    ),
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "our",
    "the",
    "their",
    "to",
    "using",
    "we",
    "will",
    "with",
    "you",
    "your",
}

DEGREE_LEVELS: dict[str, int] = {
    "diploma": 1,
    "associate": 1,
    "bachelor": 2,
    "bachelors": 2,
    "btech": 2,
    "be": 2,
    "undergraduate": 2,
    "master": 3,
    "masters": 3,
    "mtech": 3,
    "mba": 3,
    "postgraduate": 3,
    "phd": 4,
    "doctorate": 4,
    "doctoral": 4,
}

YEAR_RANGE_PATTERN = re.compile(
    r"\b(?P<start>(?:19|20)\d{2})\s*"
    r"(?:-|–|—|to)\s*"
    r"(?P<end>(?:19|20)\d{2}|present|current|now)\b",
    re.IGNORECASE,
)

EXPLICIT_YEARS_PATTERN = re.compile(
    r"\b(?P<years>\d+(?:\.\d+)?)\+?\s*"
    r"(?:years?|yrs?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class _Corpus:
    section_lines: dict[str, tuple[str, ...]]
    full_text: str
    canonical_terms: frozenset[str]


@dataclass(frozen=True, slots=True)
class _CategoryResult:
    category: MatchingCategory
    score: float
    applicable: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class _TermMatchResult:
    matched: list[str]
    missing: list[str]
    evidence: list[RequirementEvidence]


def _normalize_text(value: str) -> str:
    lowered = value.casefold()
    normalized = re.sub(
        r"[^a-z0-9+#]+",
        " ",
        lowered,
    )
    return " ".join(normalized.split())


def _alias_lookup() -> dict[str, str]:
    result: dict[str, str] = {}

    for canonical, aliases in ALIASES.items():
        result[_normalize_text(canonical)] = canonical

        for alias in aliases:
            result[_normalize_text(alias)] = canonical

    return result


ALIAS_LOOKUP = _alias_lookup()


def _canonicalize(value: str) -> str:
    normalized = _normalize_text(value)
    return ALIAS_LOOKUP.get(normalized, normalized)


def _deduplicate(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = value.strip()
        key = cleaned.casefold()

        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def _section_lines(
    resume: ResumeStructuredContent,
    raw_text: str,
) -> dict[str, tuple[str, ...]]:
    sections: dict[str, tuple[str, ...]] = {
        "summary": ((resume.summary,) if resume.summary else ()),
        "skills": tuple(resume.skills),
        "experience": tuple(resume.experience),
        "projects": tuple(resume.projects),
        "education": tuple(resume.education),
        "certifications": tuple(resume.certifications),
    }

    if raw_text.strip():
        sections["raw_text"] = tuple(line.strip() for line in raw_text.splitlines() if line.strip())

    return sections


def _build_corpus(
    resume: ResumeStructuredContent,
    raw_text: str,
) -> _Corpus:
    sections = _section_lines(resume, raw_text)
    all_lines = [line for lines in sections.values() for line in lines]
    full_text = _normalize_text("\n".join(all_lines))
    canonical_terms: set[str] = {
        _canonicalize(skill) for skill in resume.skills if _canonicalize(skill)
    }

    for alias, canonical in ALIAS_LOOKUP.items():
        if _contains_phrase(full_text, alias):
            canonical_terms.add(canonical)

    return _Corpus(
        section_lines=sections,
        full_text=full_text,
        canonical_terms=frozenset(canonical_terms),
    )


def _contains_phrase(
    normalized_text: str,
    normalized_phrase: str,
) -> bool:
    if not normalized_phrase:
        return False

    pattern = r"(?:^|\s)" + re.escape(normalized_phrase) + r"(?:$|\s)"
    return re.search(pattern, normalized_text) is not None


def _candidate_aliases(term: str) -> tuple[str, ...]:
    canonical = _canonicalize(term)
    aliases = ALIASES.get(canonical)

    if aliases is None:
        normalized = _normalize_text(term)
        return (normalized,) if normalized else ()

    values = {_normalize_text(alias) for alias in aliases}
    values.add(_normalize_text(canonical))
    return tuple(sorted(values))


def _find_term_evidence(
    *,
    display_term: str,
    corpus: _Corpus,
) -> RequirementEvidence | None:
    canonical = _canonicalize(display_term)
    aliases = _candidate_aliases(display_term)

    matched = canonical in corpus.canonical_terms or any(
        _contains_phrase(corpus.full_text, alias) for alias in aliases
    )

    if not matched:
        return None

    source_sections: list[str] = []
    excerpts: list[str] = []

    for section_name, lines in corpus.section_lines.items():
        section_matched = False

        for line in lines:
            normalized_line = _normalize_text(line)

            if any(_contains_phrase(normalized_line, alias) for alias in aliases):
                section_matched = True

                if len(excerpts) < 3:
                    excerpts.append(line)

        if section_matched:
            source_sections.append(section_name)

    if not source_sections and canonical in corpus.canonical_terms:
        source_sections.append("skills")

    return RequirementEvidence(
        requirement=display_term,
        matched_term=canonical,
        source_sections=_deduplicate(source_sections),
        excerpts=_deduplicate(excerpts),
    )


def _match_terms(
    terms: Sequence[str],
    corpus: _Corpus,
) -> _TermMatchResult:
    matched: list[str] = []
    missing: list[str] = []
    evidence: list[RequirementEvidence] = []

    for term in _deduplicate(terms):
        item = _find_term_evidence(
            display_term=term,
            corpus=corpus,
        )

        if item is None:
            missing.append(term)
        else:
            matched.append(term)
            evidence.append(item)

    return _TermMatchResult(
        matched=matched,
        missing=missing,
        evidence=evidence,
    )


def _percentage(
    matched_count: int,
    total_count: int,
) -> float:
    if total_count == 0:
        return 100.0

    return round(
        matched_count / total_count * 100,
        2,
    )


def _meaningful_tokens(value: str) -> set[str]:
    return {
        token
        for token in _normalize_text(value).split()
        if token not in STOP_WORDS and len(token) >= 2
    }


def _mentioned_canonical_terms(value: str) -> set[str]:
    normalized = _normalize_text(value)
    result: set[str] = set()

    for alias, canonical in ALIAS_LOOKUP.items():
        if _contains_phrase(normalized, alias):
            result.add(canonical)

    return result


def _line_similarity(
    responsibility: str,
    evidence_line: str,
) -> float:
    responsibility_tokens = _meaningful_tokens(responsibility)
    evidence_tokens = _meaningful_tokens(evidence_line)

    if not responsibility_tokens:
        return 0.0

    lexical_coverage = len(responsibility_tokens & evidence_tokens) / len(responsibility_tokens)

    responsibility_terms = _mentioned_canonical_terms(responsibility)
    evidence_terms = _mentioned_canonical_terms(evidence_line)

    if responsibility_terms:
        term_coverage = len(responsibility_terms & evidence_terms) / len(responsibility_terms)
        similarity = lexical_coverage * 0.55 + term_coverage * 0.45
    else:
        similarity = lexical_coverage

    return min(similarity, 1.0)


def _match_responsibilities(
    responsibilities: Sequence[str],
    resume: ResumeStructuredContent,
) -> tuple[list[ResponsibilityMatch], float]:
    evidence_lines = _deduplicate(
        [
            *resume.experience,
            *resume.projects,
            *([resume.summary] if resume.summary else []),
        ]
    )
    results: list[ResponsibilityMatch] = []

    for responsibility in _deduplicate(responsibilities):
        best_line: str | None = None
        best_similarity = 0.0

        for line in evidence_lines:
            similarity = _line_similarity(
                responsibility,
                line,
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_line = line

        score = round(
            best_similarity * 100,
            2,
        )

        status: ResponsibilityStatus

        if score >= 60:
            status = "aligned"
        elif score >= 25:
            status = "partially_aligned"
        else:
            status = "not_aligned"
            best_line = None

        results.append(
            ResponsibilityMatch(
                responsibility=responsibility,
                status=status,
                score=score,
                evidence=best_line,
            )
        )

    if not results:
        return [], 100.0

    average = round(
        sum(item.score for item in results) / len(results),
        2,
    )
    return results, average


def _merge_intervals(
    intervals: Sequence[tuple[int, int]],
) -> list[tuple[int, int]]:
    if not intervals:
        return []

    ordered = sorted(intervals)
    merged: list[tuple[int, int]] = [ordered[0]]

    for start, end in ordered[1:]:
        previous_start, previous_end = merged[-1]

        if start <= previous_end:
            merged[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged.append((start, end))

    return merged


def _estimate_experience_years(
    resume: ResumeStructuredContent,
    raw_text: str,
    reference_year: int,
) -> float | None:
    text = "\n".join(
        [
            *(resume.experience),
            *(resume.projects),
            *([resume.summary] if resume.summary else []),
            raw_text,
        ]
    )

    explicit_values = [
        float(match.group("years")) for match in EXPLICIT_YEARS_PATTERN.finditer(text)
    ]

    intervals: list[tuple[int, int]] = []

    for match in YEAR_RANGE_PATTERN.finditer(text):
        start = int(match.group("start"))
        end_text = match.group("end").casefold()
        end = (
            reference_year
            if end_text
            in {
                "present",
                "current",
                "now",
            }
            else int(end_text)
        )

        if start <= end <= reference_year:
            intervals.append((start, end))

    merged = _merge_intervals(intervals)
    interval_years = sum(end - start for start, end in merged)
    candidates = list(explicit_values)

    if interval_years > 0:
        candidates.append(float(interval_years))

    return max(candidates) if candidates else None


def _compare_experience(
    *,
    job: ParsedJobDescription,
    resume: ResumeStructuredContent,
    raw_text: str,
    candidate_override: float | None,
    reference_year: int,
) -> ExperienceComparison:
    required_min = job.experience.min_years
    required_max = job.experience.max_years
    applicable = (
        required_min is not None or required_max is not None or job.experience.statement is not None
    )

    if not applicable:
        return ExperienceComparison(
            status="not_specified",
            required_min_years=None,
            required_max_years=None,
            candidate_years=candidate_override,
            score=100,
            explanation=("The job description does not specify an experience requirement."),
        )

    candidate_years = (
        candidate_override
        if candidate_override is not None
        else _estimate_experience_years(
            resume,
            raw_text,
            reference_year,
        )
    )

    if candidate_years is None:
        return ExperienceComparison(
            status="unknown",
            required_min_years=required_min,
            required_max_years=required_max,
            candidate_years=None,
            score=40,
            explanation=(
                "The resume does not contain enough information to estimate total experience."
            ),
        )

    minimum = required_min or 0

    if candidate_years >= minimum:
        return ExperienceComparison(
            status="met",
            required_min_years=required_min,
            required_max_years=required_max,
            candidate_years=round(
                candidate_years,
                2,
            ),
            score=100,
            explanation=(
                f"Estimated experience ({candidate_years:g} years) "
                f"meets the minimum requirement ({minimum} years)."
            ),
        )

    ratio = candidate_years / minimum if minimum > 0 else 1.0
    score = round(
        min(ratio * 100, 99),
        2,
    )
    status: RequirementStatus = "partially_met" if ratio >= 0.7 else "not_met"

    return ExperienceComparison(
        status=status,
        required_min_years=required_min,
        required_max_years=required_max,
        candidate_years=round(
            candidate_years,
            2,
        ),
        score=score,
        explanation=(
            f"Estimated experience ({candidate_years:g} years) "
            f"is below the minimum requirement ({minimum} years)."
        ),
    )


def _highest_degree_level(
    values: Sequence[str],
) -> tuple[str | None, int | None]:
    best_name: str | None = None
    best_rank: int | None = None

    for value in values:
        normalized_value = _normalize_text(value)
        tokens = _meaningful_tokens(value)
        expanded_tokens = set(tokens)

        for phrase in ("b tech", "b e"):
            if _contains_phrase(normalized_value, phrase):
                expanded_tokens.add("btech")

        for phrase in ("m tech", "m e"):
            if _contains_phrase(normalized_value, phrase):
                expanded_tokens.add("mtech")

        for name, rank in DEGREE_LEVELS.items():
            if name in expanded_tokens and (best_rank is None or rank > best_rank):
                best_name = name
                best_rank = rank

    return best_name, best_rank


def _education_field_tokens(
    values: Sequence[str],
) -> set[str]:
    degree_words = set(DEGREE_LEVELS)
    generic_words = {
        "degree",
        "education",
        "field",
        "related",
        "required",
        "requirement",
    }
    result: set[str] = set()

    for value in values:
        result.update(
            token
            for token in _meaningful_tokens(value)
            if token not in degree_words and token not in generic_words
        )

    return result


def _compare_education(
    *,
    job: ParsedJobDescription,
    resume: ResumeStructuredContent,
) -> EducationComparison:
    requirements = _deduplicate(job.education_requirements)

    if not requirements:
        return EducationComparison(
            status="not_specified",
            score=100,
            explanation=("The job description does not specify an education requirement."),
        )

    required_name, required_rank = _highest_degree_level(requirements)
    candidate_name, candidate_rank = _highest_degree_level(resume.education)

    if not resume.education:
        return EducationComparison(
            status="unknown",
            required_level=required_name,
            candidate_level=None,
            score=30,
            explanation=("The resume does not contain an education section."),
        )

    required_fields = _education_field_tokens(requirements)
    candidate_fields = _education_field_tokens(resume.education)
    field_overlap = (
        len(required_fields & candidate_fields) / len(required_fields) if required_fields else 1.0
    )

    status: RequirementStatus
    score: float
    explanation: str

    if required_rank is not None:
        if candidate_rank is not None and candidate_rank >= required_rank:
            score = 100.0 if field_overlap >= 0.5 else 85.0
            status = "met" if score == 100 else "partially_met"
            explanation = (
                "The resume meets the degree-level requirement."
                if score == 100
                else (
                    "The degree level is met, but the required field is not clearly demonstrated."
                )
            )
        else:
            score = 25.0
            status = "not_met"
            explanation = "The resume does not demonstrate the required degree level."
    else:
        score = round(
            field_overlap * 100,
            2,
        )

        if score >= 60:
            status = "met"
        elif score >= 25:
            status = "partially_met"
        else:
            status = "not_met"

        explanation = "Education requirements were compared using deterministic keyword overlap."

    return EducationComparison(
        status=status,
        required_level=required_name,
        candidate_level=candidate_name,
        score=score,
        explanation=explanation,
    )


def _category_scores(
    categories: Sequence[_CategoryResult],
) -> list[MatchCategoryScore]:
    applicable_weight = sum(
        CATEGORY_WEIGHTS[item.category] for item in categories if item.applicable
    )
    results: list[MatchCategoryScore] = []

    for item in categories:
        configured_weight = CATEGORY_WEIGHTS[item.category]
        effective_weight = (
            configured_weight / applicable_weight
            if item.applicable and applicable_weight > 0
            else 0.0
        )
        weighted_points = item.score * effective_weight
        results.append(
            MatchCategoryScore(
                category=item.category,
                raw_score=round(item.score, 2),
                configured_weight=configured_weight,
                effective_weight=round(
                    effective_weight,
                    4,
                ),
                weighted_points=round(
                    weighted_points,
                    2,
                ),
                applicable=item.applicable,
                explanation=item.explanation,
            )
        )

    return results


def _overall_score(
    breakdown: Sequence[MatchCategoryScore],
) -> float:
    return round(
        sum(item.weighted_points for item in breakdown),
        2,
    )


def _build_strengths(
    *,
    required: _TermMatchResult,
    preferred: _TermMatchResult,
    technologies: _TermMatchResult,
    experience: ExperienceComparison,
    education: EducationComparison,
    responsibility_score: float,
) -> list[str]:
    strengths: list[str] = []

    if required.matched and not required.missing:
        strengths.append("All explicitly required skills are demonstrated.")
    elif required.matched:
        strengths.append(
            "The resume demonstrates several required skills: "
            + ", ".join(required.matched[:5])
            + "."
        )

    if preferred.matched:
        strengths.append("Preferred skills present: " + ", ".join(preferred.matched[:5]) + ".")

    if technologies.matched:
        strengths.append(
            "Relevant technologies demonstrated: " + ", ".join(technologies.matched[:5]) + "."
        )

    if experience.status == "met":
        strengths.append("The estimated experience meets the job requirement.")

    if education.status == "met":
        strengths.append("The education requirement is demonstrated.")

    if responsibility_score >= 70:
        strengths.append("Resume experience aligns strongly with the listed responsibilities.")

    return _deduplicate(strengths)


def _build_weaknesses(
    *,
    required: _TermMatchResult,
    preferred: _TermMatchResult,
    technologies: _TermMatchResult,
    experience: ExperienceComparison,
    education: EducationComparison,
    responsibility_score: float,
    responsibilities_present: bool,
) -> list[str]:
    weaknesses: list[str] = []

    if required.missing:
        weaknesses.append("Missing required skills: " + ", ".join(required.missing[:8]) + ".")

    if preferred.missing:
        weaknesses.append(
            "Preferred skills not demonstrated: " + ", ".join(preferred.missing[:8]) + "."
        )

    if technologies.missing:
        weaknesses.append(
            "Technologies not demonstrated: " + ", ".join(technologies.missing[:8]) + "."
        )

    if experience.status in {
        "partially_met",
        "not_met",
    }:
        weaknesses.append(experience.explanation)

    if education.status in {
        "partially_met",
        "not_met",
    }:
        weaknesses.append(education.explanation)

    if responsibilities_present and responsibility_score < 40:
        weaknesses.append("The resume provides limited evidence for the listed responsibilities.")

    return _deduplicate(weaknesses)


def _build_warnings(
    *,
    request: ResumeJobMatchRequest,
    experience: ExperienceComparison,
    education: EducationComparison,
    applicable_categories: int,
) -> list[str]:
    warnings: list[str] = []

    if not request.resume.skills:
        warnings.append("The parsed resume contains no explicit skills section.")

    if not request.job_description.required_skills:
        warnings.append("The job description contains no explicit required-skills list.")

    if experience.status == "unknown":
        warnings.append(
            "Experience alignment is uncertain because total candidate "
            "experience could not be estimated."
        )

    if education.status == "unknown":
        warnings.append(
            "Education alignment is uncertain because the resume education section is missing."
        )

    if applicable_categories == 0:
        warnings.append("The job description contains no matchable requirements.")

    return _deduplicate(warnings)


class ResumeJobMatcher:
    def __init__(
        self,
        *,
        reference_year: int | None = None,
    ) -> None:
        self._reference_year = (
            reference_year if reference_year is not None else datetime.now(UTC).year
        )

    def match(
        self,
        request: ResumeJobMatchRequest,
    ) -> ResumeJobMatchResult:
        resume = request.resume
        job = request.job_description
        corpus = _build_corpus(
            resume,
            request.resume_raw_text,
        )

        required = _match_terms(
            job.required_skills,
            corpus,
        )
        preferred = _match_terms(
            job.preferred_skills,
            corpus,
        )
        technologies = _match_terms(
            job.technologies,
            corpus,
        )
        keywords = _match_terms(
            job.ats_keywords,
            corpus,
        )

        responsibility_alignment, responsibility_score = _match_responsibilities(
            job.responsibilities,
            resume,
        )
        experience = _compare_experience(
            job=job,
            resume=resume,
            raw_text=request.resume_raw_text,
            candidate_override=(request.candidate_experience_years),
            reference_year=self._reference_year,
        )
        education = _compare_education(
            job=job,
            resume=resume,
        )

        required_score = _percentage(
            len(required.matched),
            len(required.matched) + len(required.missing),
        )
        preferred_score = _percentage(
            len(preferred.matched),
            len(preferred.matched) + len(preferred.missing),
        )
        technology_score = _percentage(
            len(technologies.matched),
            len(technologies.matched) + len(technologies.missing),
        )
        keyword_score = _percentage(
            len(keywords.matched),
            len(keywords.matched) + len(keywords.missing),
        )

        categories = [
            _CategoryResult(
                category="required_skills",
                score=required_score,
                applicable=bool(job.required_skills),
                explanation=("Share of required skills demonstrated by the resume."),
            ),
            _CategoryResult(
                category="preferred_skills",
                score=preferred_score,
                applicable=bool(job.preferred_skills),
                explanation=("Share of preferred skills demonstrated by the resume."),
            ),
            _CategoryResult(
                category="technologies",
                score=technology_score,
                applicable=bool(job.technologies),
                explanation=("Share of job technologies found in resume evidence."),
            ),
            _CategoryResult(
                category="ats_keywords",
                score=keyword_score,
                applicable=bool(job.ats_keywords),
                explanation=("Share of ATS keywords found in resume evidence."),
            ),
            _CategoryResult(
                category="experience",
                score=experience.score,
                applicable=(experience.status != "not_specified"),
                explanation=experience.explanation,
            ),
            _CategoryResult(
                category="education",
                score=education.score,
                applicable=(education.status != "not_specified"),
                explanation=education.explanation,
            ),
            _CategoryResult(
                category="responsibilities",
                score=responsibility_score,
                applicable=bool(job.responsibilities),
                explanation=(
                    "Average deterministic alignment between job "
                    "responsibilities and resume evidence."
                ),
            ),
        ]
        breakdown = _category_scores(categories)
        applicable_categories = sum(item.applicable for item in categories)
        evidence = [
            *required.evidence,
            *preferred.evidence,
            *technologies.evidence,
            *keywords.evidence,
        ]

        return ResumeJobMatchResult(
            overall_match_score=_overall_score(breakdown),
            required_skills_score=required_score,
            preferred_skills_score=preferred_score,
            technology_score=technology_score,
            keyword_score=keyword_score,
            experience_score=experience.score,
            education_score=education.score,
            responsibility_score=responsibility_score,
            matched_required_skills=required.matched,
            missing_required_skills=required.missing,
            matched_preferred_skills=preferred.matched,
            missing_preferred_skills=preferred.missing,
            matched_technologies=technologies.matched,
            missing_technologies=technologies.missing,
            matched_keywords=keywords.matched,
            missing_keywords=keywords.missing,
            experience=experience,
            education=education,
            responsibility_alignment=(responsibility_alignment),
            strengths=_build_strengths(
                required=required,
                preferred=preferred,
                technologies=technologies,
                experience=experience,
                education=education,
                responsibility_score=(responsibility_score),
            ),
            weaknesses=_build_weaknesses(
                required=required,
                preferred=preferred,
                technologies=technologies,
                experience=experience,
                education=education,
                responsibility_score=(responsibility_score),
                responsibilities_present=bool(job.responsibilities),
            ),
            resume_evidence=evidence,
            warnings=_build_warnings(
                request=request,
                experience=experience,
                education=education,
                applicable_categories=(applicable_categories),
            ),
            scoring_breakdown=breakdown,
            metadata=ResumeMatchingMetadata(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                deterministic=True,
                compared_requirements=sum(
                    len(values)
                    for values in (
                        job.required_skills,
                        job.preferred_skills,
                        job.technologies,
                        job.ats_keywords,
                        job.responsibilities,
                        job.education_requirements,
                    )
                )
                + int(experience.status != "not_specified"),
                generated_evidence_items=len(evidence),
            ),
        )


def match_resume_to_job(
    *,
    resume: ResumeStructuredContent,
    job_description: ParsedJobDescription,
    resume_raw_text: str = "",
    candidate_experience_years: float | None = None,
    reference_year: int | None = None,
) -> ResumeJobMatchResult:
    matcher = ResumeJobMatcher(reference_year=reference_year)
    request = ResumeJobMatchRequest(
        resume=resume,
        job_description=job_description,
        resume_raw_text=resume_raw_text,
        candidate_experience_years=(candidate_experience_years),
    )
    return matcher.match(request)
