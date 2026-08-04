# Resume API, Viewer, and History

## Day 6 Scope

Day 6 exposes the Day 5 parser through a complete authenticated resume API and adds viewer, history, original-file access, and deletion workflows.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/resume/{resume_id}/parse` | Parse an uploaded resume |
| `GET` | `/api/v1/resume/{resume_id}/parsed` | Retrieve the persisted parsed result |
| `GET` | `/api/v1/resume/{resume_id}/parse-status` | Retrieve parsing status and error information |
| `GET` | `/api/v1/resume/history` | List the authenticated user's resume history |
| `GET` | `/api/v1/resume/{resume_id}` | Retrieve resume metadata |
| `GET` | `/api/v1/resume/{resume_id}/viewer` | Retrieve viewer-ready parsed content |
| `GET` | `/api/v1/resume/{resume_id}/file` | Download the original private resume file |
| `DELETE` | `/api/v1/resume/{resume_id}` | Delete metadata, parse result, and stored file |

All endpoints require a valid JWT access token.

## Resume History

The history endpoint supports pagination:

```text
GET /api/v1/resume/history?page=1&page_size=20
```

Rules:

- `page` must be at least 1.
- `page_size` must be between 1 and 100.
- Results are ordered by upload time from newest to oldest.
- Only resumes owned by the authenticated user are returned.

## Resume Viewer

The viewer endpoint returns:

- Resume metadata
- Parsing status
- Contact information
- Summary
- Skills
- Education
- Experience
- Projects
- Certifications
- Raw extracted text
- Parser metadata
- OCR requirement
- Parsing warnings

For a resume that has not been parsed, the viewer returns the resume metadata with `content`, `raw_text`, and `metadata` set to `null`.

## Original File Access

The file endpoint reads the private object through the configured storage abstraction. It works with both local storage and AWS S3.

The response includes:

- The validated content type
- A safe `Content-Disposition` download header
- An `X-Content-SHA256` integrity header

Private storage keys and bucket details are never exposed.

## Deletion Workflow

Deletion performs the following steps:

1. Verify authenticated ownership.
2. Read the stored file for rollback protection.
3. Delete the physical local or S3 object.
4. Delete the database resume record.
5. Cascade-delete the parsed result.
6. Commit the transaction.
7. Restore the file when the database commit fails, when possible.

This compensating workflow reduces inconsistent database and object-storage state.

## Database Migration

Day 6 requires no new migration. The existing Day 4 and Day 5 tables already contain the metadata, ownership, parsing status, and parsed result required by this API.

Current Alembic head remains:

```text
20260803_0003 (head)
```

## Testing

Day 6 tests cover:

- Paginated history
- Resume detail
- Parse status
- Parsed and unparsed viewer responses
- Original-file retrieval
- Ownership enforcement
- Authentication enforcement
- Pagination validation
- Physical-file deletion
- Database record deletion
- Storage failures
- Database failure compensation
