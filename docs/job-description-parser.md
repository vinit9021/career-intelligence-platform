# Job Description Parser

## Day 8 Scope

Day 8 adds a deterministic job-description parser. It does not add an API, database model, migration, history, matching engine, ATS score, embeddings, or LangGraph workflow.

## Input

The parser accepts plain job-description text.

It:

- rejects empty input;
- rejects input longer than 60,000 characters;
- removes unsafe control characters;
- normalizes line endings and repeated whitespace;
- preserves meaningful line and section boundaries.

## Extracted Structure

The parser returns Pydantic JSON containing:

- job title;
- company name when present;
- required skills;
- preferred skills;
- technologies and tools;
- responsibilities;
- qualifications;
- experience requirement;
- education requirements;
- seniority level;
- ATS keywords;
- normalized source text;
- parser metadata and warnings.

## Supported Section Headings

The parser recognizes common headings such as:

- Required Skills
- Must Have
- Preferred Skills
- Nice to Have
- Responsibilities
- What You Will Do
- Qualifications
- Requirements
- Education
- Experience

## Deterministic Parsing

Day 8 intentionally uses deterministic rules rather than an LLM. This keeps the output:

- testable;
- reproducible;
- inexpensive;
- suitable as stable input for the later resume-matching engine.

## Usage

```python
from app.parsers import JobDescriptionParser

parser = JobDescriptionParser()
result = parser.parse(job_description_text)
payload = result.model_dump(mode="json")
```

A function interface is also available:

```python
from app.parsers import parse_job_description

result = parse_job_description(job_description_text)
```

## Error Types

- `EmptyJobDescriptionError`
- `JobDescriptionTooLargeError`
- `JobDescriptionParserError`

## Seniority Values

```text
intern
entry
mid
senior
lead
manager
director
executive
unspecified
```

## Verification

Run from the `backend` directory:

```powershell
ruff format app tests migrations scripts
ruff check app tests migrations scripts
ruff format --check app tests migrations scripts
mypy app tests
pytest tests/unit/test_job_description_parser.py tests/unit/test_job_description_schema.py -v --no-cov
pytest
```

The complete test suite must continue to satisfy the repository coverage threshold.
