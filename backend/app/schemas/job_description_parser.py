from typing import Literal

from pydantic import BaseModel, Field

JobSeniorityLevel = Literal[
    "intern",
    "entry",
    "mid",
    "senior",
    "lead",
    "manager",
    "director",
    "executive",
    "unspecified",
]


class JobExperienceRequirement(BaseModel):
    min_years: int | None = Field(
        default=None,
        ge=0,
        le=60,
    )
    max_years: int | None = Field(
        default=None,
        ge=0,
        le=60,
    )
    statement: str | None = None


class JobDescriptionParserMetadata(BaseModel):
    parser_name: str
    parser_version: str
    character_count: int = Field(ge=1)
    warnings: list[str] = Field(default_factory=list)


class ParsedJobDescription(BaseModel):
    job_title: str | None = None
    company_name: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    experience: JobExperienceRequirement = Field(default_factory=JobExperienceRequirement)
    education_requirements: list[str] = Field(default_factory=list)
    seniority_level: JobSeniorityLevel = "unspecified"
    ats_keywords: list[str] = Field(default_factory=list)
    normalized_text: str = Field(min_length=1)
    metadata: JobDescriptionParserMetadata
