# Resume Parsing Architecture

## Scope

Day 5 adds deterministic PDF and DOCX text extraction, parser selection, OCR readiness detection, structured resume JSON, persistence, and protected parse APIs.

The parser extracts contact details and recognized sections for skills, education, experience, projects, certifications, and summary. It does not rewrite facts or call an LLM.

## Endpoints

```text
POST /api/v1/resume/{resume_id}/parse
GET  /api/v1/resume/{resume_id}/parsed
```

Both endpoints require JWT authentication and enforce resume ownership.

## Parser Flow

1. Load the owned resume metadata.
2. Read the private file through the storage abstraction.
3. Select the PDF or DOCX parser.
4. Extract text in document order.
5. Detect image-only or low-text content.
6. Build structured Pydantic output.
7. Persist raw text, structured content, parser metadata, and warnings.
8. Mark the resume as `completed`, `needs_ocr`, or `failed`.

## OCR Preparation

Day 5 does not run OCR. Low-text documents are marked `needs_ocr` and include a warning so a later background OCR worker can process them.

## Structured Output

The response contains:

- Contact information
- Summary
- Skills
- Education
- Experience
- Projects
- Certifications
- Raw extracted text
- Parser name and version
- Page count when available
- Character count
- OCR requirement
- Warnings

## Database

Migration:

```text
20260803_0003_add_resume_parsing
```

New table:

```text
resume_parse_results
```

New `resumes` fields:

- `parse_status`
- `parse_error`
- `parsed_at`

## Non-Scope

- OCR execution
- ATS scoring
- Semantic matching
- Embeddings
- Resume rewriting
- LangGraph orchestration
