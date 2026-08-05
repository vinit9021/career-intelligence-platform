# Resume Matching Engine

## Day 9 Scope

Day 9 adds a deterministic and explainable engine that compares the structured resume output with the structured job-description output.

It does not add an API, database model, migration, embeddings, LLM calls, or ATS rewriting.

## Inputs

The engine consumes:

- `ResumeStructuredContent` from the resume parser
- `ParsedJobDescription` from the job-description parser
- Optional raw resume text
- Optional explicit candidate experience in years

## Matching Dimensions

The engine evaluates:

1. Required skills
2. Preferred skills
3. Technologies and tools
4. ATS keywords
5. Experience requirement
6. Education requirement
7. Responsibility alignment

## Alias Normalization

Common aliases are matched deterministically, including:

- PostgreSQL / Postgres
- AWS / Amazon Web Services
- JavaScript / JS
- Kubernetes / k8s
- C++ / cpp
- C# / C Sharp
- REST API / RESTful API
- SQL / Structured Query Language

## Scoring Weights

| Category | Configured weight |
|---|---:|
| Required skills | 30% |
| Preferred skills | 10% |
| Technologies | 15% |
| ATS keywords | 15% |
| Experience | 10% |
| Education | 5% |
| Responsibilities | 15% |

When a job description does not specify a category, that category is marked non-applicable. Its weight is redistributed proportionally across the applicable categories.

## Experience Matching

Candidate experience is determined in this order:

1. Explicit `candidate_experience_years` input
2. Explicit phrases such as `3 years of experience`
3. Resume date ranges such as `2021 - Present`

The result is classified as:

- `met`
- `partially_met`
- `not_met`
- `unknown`
- `not_specified`

## Education Matching

The matcher compares deterministic degree levels:

```text
Diploma/Associate < Bachelor < Master < Doctorate
```

It also checks field-related keyword overlap when a field is stated.

## Responsibility Alignment

Each job responsibility is compared with resume experience, project, and summary lines.

The engine returns:

- Alignment score
- `aligned`, `partially_aligned`, or `not_aligned`
- Best supporting resume evidence

This is deterministic lexical and alias-aware alignment. It is not embedding-based semantic similarity.

## Structured Result

The output includes:

```text
overall_match_score
required_skills_score
preferred_skills_score
technology_score
keyword_score
experience_score
education_score
responsibility_score
matched_required_skills
missing_required_skills
matched_preferred_skills
missing_preferred_skills
matched_technologies
missing_technologies
matched_keywords
missing_keywords
experience
education
responsibility_alignment
strengths
weaknesses
resume_evidence
warnings
scoring_breakdown
metadata
```

## Usage

```python
from app.matching import match_resume_to_job

result = match_resume_to_job(
    resume=parsed_resume.content,
    job_description=parsed_job_description,
    resume_raw_text=parsed_resume.raw_text,
)

payload = result.model_dump(mode="json")
```

## Day 9 Non-Scope

- API endpoints
- Database persistence
- Match-report history
- ATS resume rewriting
- Resume optimization
- Resume version creation
- Embeddings or FAISS
- LLM calls
- LangGraph orchestration
