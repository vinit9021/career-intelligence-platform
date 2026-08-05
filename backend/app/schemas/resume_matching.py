from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.job_description_parser import ParsedJobDescription
from app.schemas.resume_parsing import ResumeStructuredContent

MatchingCategory = Literal[
    "required_skills",
    "preferred_skills",
    "technologies",
    "ats_keywords",
    "experience",
    "education",
    "responsibilities",
]

RequirementStatus = Literal[
    "met",
    "partially_met",
    "not_met",
    "unknown",
    "not_specified",
]

ResponsibilityStatus = Literal[
    "aligned",
    "partially_aligned",
    "not_aligned",
]


class ResumeJobMatchRequest(BaseModel):
    resume: ResumeStructuredContent
    job_description: ParsedJobDescription
    resume_raw_text: str = ""
    candidate_experience_years: float | None = Field(
        default=None,
        ge=0,
        le=60,
    )


class RequirementEvidence(BaseModel):
    requirement: str
    matched_term: str
    source_sections: list[str] = Field(default_factory=list)
    excerpts: list[str] = Field(default_factory=list)


class ResponsibilityMatch(BaseModel):
    responsibility: str
    status: ResponsibilityStatus
    score: float = Field(ge=0, le=100)
    evidence: str | None = None


class ExperienceComparison(BaseModel):
    status: RequirementStatus
    required_min_years: int | None = None
    required_max_years: int | None = None
    candidate_years: float | None = Field(
        default=None,
        ge=0,
        le=60,
    )
    score: float = Field(ge=0, le=100)
    explanation: str


class EducationComparison(BaseModel):
    status: RequirementStatus
    required_level: str | None = None
    candidate_level: str | None = None
    score: float = Field(ge=0, le=100)
    explanation: str


class MatchCategoryScore(BaseModel):
    category: MatchingCategory
    raw_score: float = Field(ge=0, le=100)
    configured_weight: float = Field(ge=0, le=1)
    effective_weight: float = Field(ge=0, le=1)
    weighted_points: float = Field(ge=0, le=100)
    applicable: bool
    explanation: str


class ResumeMatchingMetadata(BaseModel):
    engine_name: str
    engine_version: str
    deterministic: bool = True
    compared_requirements: int = Field(ge=0)
    generated_evidence_items: int = Field(ge=0)


class ResumeJobMatchResult(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    overall_match_score: float = Field(ge=0, le=100)
    required_skills_score: float = Field(ge=0, le=100)
    preferred_skills_score: float = Field(ge=0, le=100)
    technology_score: float = Field(ge=0, le=100)
    keyword_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    education_score: float = Field(ge=0, le=100)
    responsibility_score: float = Field(ge=0, le=100)

    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    matched_technologies: list[str] = Field(default_factory=list)
    missing_technologies: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)

    experience: ExperienceComparison
    education: EducationComparison
    responsibility_alignment: list[ResponsibilityMatch] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    resume_evidence: list[RequirementEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    scoring_breakdown: list[MatchCategoryScore]
    metadata: ResumeMatchingMetadata
