# Career Intelligence Platform

Career Intelligence Platform is an AI-powered job-search operating system that
manages resume intelligence, job matching, application tracking, online
assessment preparation, interview preparation, recruiter communication, and
career analytics.

## Current Development Status

**Week 1, Day 1 — Project Foundation**

Implemented:

- FastAPI backend foundation
- Next.js frontend foundation
- Versioned API routing
- Health-check endpoint
- Environment configuration
- Logging configuration
- Backend testing and coverage
- Type checking
- Linting and formatting
- React Query provider
- Tailwind CSS
- Project documentation

## Technology Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- LangGraph
- Celery
- FAISS

### Frontend

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- TanStack React Query

### Infrastructure

- Docker
- AWS S3
- GitHub
- OpenTelemetry
- Grafana

## Repository Structure

```text
career-intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── prompts/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tools/
│   │   └── workflows/
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── lib/
│   │   └── providers/
│   ├── package.json
│   └── next.config.ts
├── docker/
├── docs/
│   └── architecture.md
├── infra/
└── README.md
```

## Prerequisites

Install:

- Python 3.12
- Node.js
- npm
- PostgreSQL
- Git
- GitHub CLI
- Visual Studio Code

Docker Desktop will be used during later infrastructure and deployment
milestones.

## Backend Setup

Open PowerShell from the repository root:

```powershell
cd backend

py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements-dev.txt

Copy-Item .env.example .env -Force
```

Start the backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

```text
API documentation: http://127.0.0.1:8000/docs
ReDoc:             http://127.0.0.1:8000/redoc
Health endpoint:   http://127.0.0.1:8000/api/v1/health
```

Expected health response:

```json
{
  "status": "ok",
  "service": "Career Intelligence Platform API",
  "environment": "development",
  "version": "0.1.0"
}
```

## Backend Quality Checks

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

ruff format app tests
ruff check app tests
ruff format --check app tests
mypy app tests
pytest
```

Expected result:

```text
Ruff checks pass
MyPy reports no issues
All tests pass
Coverage remains at or above 90%
```

## Frontend Setup

From the repository root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local -Force
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Frontend Quality Checks

```powershell
cd frontend

npm run format
npm run lint
npm run type-check
npm run format:check
npm run build
```

Expected result:

```text
Prettier passes
ESLint passes
TypeScript passes
Next.js production build succeeds
```

## Environment Variables

### Backend

Create `backend/.env` from `backend/.env.example`.

```dotenv
APP_NAME=Career Intelligence Platform API
APP_ENV=development
APP_VERSION=0.1.0
API_V1_PREFIX=/api/v1
DEBUG=true
LOG_LEVEL=INFO
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend

Create `frontend/.env.local` from `frontend/.env.example`.

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Local environment files must never be committed to Git.

## Architecture Documentation

Detailed architecture information is available in:

```text
docs/architecture.md
```

## Development Roadmap

The platform will be implemented incrementally:

1. Project foundation
2. Authentication and user profiles
3. PostgreSQL and repository layer
4. Resume upload and storage
5. Resume parsing
6. Job intelligence
7. Agentic AI workflows
8. Dashboard
9. Gmail synchronization
10. OA preparation
11. Interview preparation
12. Analytics and notifications
13. Production infrastructure
14. Testing and deployment

## Next Milestone

**Week 1, Day 2 — Authentication**

The next milestone will implement:

- Authentication architecture
- User registration
- User login
- Password hashing
- JWT access tokens
- Refresh tokens
- Protected routes
- Request and response schemas
- Authentication error handling
- Unit and integration tests

## Day 2 Authentication

Implemented:

- User registration
- User login
- Argon2 password hashing
- JWT access tokens
- JWT refresh tokens
- Refresh-token rotation
- Protected current-user route
- Authentication validation
- Authentication unit and integration tests

Authentication documentation:

docs/authentication.md

## Day 3 — Database Persistence and Profile CRUD

Day 3 introduces persistent PostgreSQL storage, Alembic migrations, a repository layer, and authenticated user/profile management.

### Implemented

- PostgreSQL integration using SQLAlchemy 2.0
- Asynchronous database access using `asyncpg`
- Async SQLAlchemy engine and session management
- Alembic migration configuration
- Initial production database migration
- Repository pattern for user and profile persistence
- One-to-one user profile model
- Authenticated current-user CRUD operations
- Authenticated profile CRUD operations
- Pydantic validation for user and profile requests
- Unit and integration tests for models, schemas, services, APIs, repositories, and migrations

### Database Tables

| Table             | Purpose                                                     |
| ----------------- | ----------------------------------------------------------- |
| `users`           | Stores user account and authentication information          |
| `profiles`        | Stores one career profile for each user                     |
| `refresh_tokens`  | Stores hashed refresh-token records used for token rotation |
| `alembic_version` | Tracks the currently applied Alembic migration              |

### Database Relationships

- One user can have one profile.
- One user can have multiple refresh-token records.
- Deleting a user automatically deletes the related profile.
- Deleting a user automatically deletes the related refresh-token records.

### User Endpoints

| Method   | Endpoint           | Description                                        |
| -------- | ------------------ | -------------------------------------------------- |
| `GET`    | `/api/v1/users/me` | Retrieve the authenticated user                    |
| `PATCH`  | `/api/v1/users/me` | Update the authenticated user's email or full name |
| `DELETE` | `/api/v1/users/me` | Delete the authenticated user's account            |

### Profile Endpoints

| Method   | Endpoint                   | Description                                       |
| -------- | -------------------------- | ------------------------------------------------- |
| `POST`   | `/api/v1/users/me/profile` | Create the authenticated user's profile           |
| `GET`    | `/api/v1/users/me/profile` | Retrieve the authenticated user's profile         |
| `PATCH`  | `/api/v1/users/me/profile` | Partially update the authenticated user's profile |
| `DELETE` | `/api/v1/users/me/profile` | Delete the authenticated user's profile           |

All user and profile endpoints require a valid JWT access token.

### Profile Information

The profile currently supports:

- Professional headline
- Location
- Phone number
- Professional biography
- Years of experience
- Target roles
- Skills
- LinkedIn URL
- GitHub URL
- Portfolio URL

### Current Migration

```text
20260803_0001_create_users_profiles_and_refresh_tokens
```

## Day 4 — Resume Upload and Storage Foundation

Day 4 adds secure resume uploading, configurable storage backends, AWS S3 integration, and persistent resume metadata.

### Implemented

- JWT-protected resume upload endpoint
- PDF and DOCX file support
- File-extension and internal file validation
- Configurable maximum upload size
- Local filesystem storage
- AWS S3 storage
- Common storage-provider abstraction
- Generated private storage keys
- SHA-256 file checksums
- S3 server-side encryption
- Resume metadata persistence
- File cleanup when database persistence fails
- Unit and integration tests

Resume parsing, text extraction, ATS scoring, embeddings, and AI-agent processing are not included in Day 4.

### Resume Upload Endpoint

| Method | Endpoint                | Description                 |
| ------ | ----------------------- | --------------------------- |
| `POST` | `/api/v1/resume/upload` | Upload a PDF or DOCX resume |

The endpoint requires a valid JWT access token.

The request must use `multipart/form-data` with a file field named:

```text
file
```

### Supported Formats

- PDF (`.pdf`)
- DOCX (`.docx`)

The backend validates both the filename extension and the internal file structure.

### Upload Size Limit

The default maximum file size is 10 MB.

```env
RESUME_MAX_SIZE_MB=10
```

### Storage Backends

The active storage backend is selected using `STORAGE_BACKEND`.

Local development configuration:

```env
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=storage
```

AWS S3 configuration:

```env
STORAGE_BACKEND=s3
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your-private-resume-bucket
```

Optional AWS settings:

```env
AWS_S3_ENDPOINT_URL=
AWS_S3_KMS_KEY_ID=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
```

When explicit AWS credentials are not provided, Boto3 can use its standard AWS credential resolution chain.

### Storage Key Format

Uploaded resumes use generated storage keys:

```text
resumes/{user_id}/{resume_id}/original.{extension}
```

The original uploaded filename is stored separately in the database.

Internal local paths and S3 storage keys are not exposed in the public API response.

### Resume Database Model

Resume metadata is stored in the `resumes` table.

| Column              | Purpose                     |
| ------------------- | --------------------------- |
| `id`                | Unique resume identifier    |
| `user_id`           | Resume owner identifier     |
| `original_filename` | Original uploaded filename  |
| `storage_backend`   | Local or S3 storage backend |
| `storage_key`       | Internal storage object key |
| `storage_etag`      | Storage ETag or checksum    |
| `content_type`      | Validated content type      |
| `file_extension`    | Validated file extension    |
| `file_size_bytes`   | Uploaded file size          |
| `sha256`            | SHA-256 checksum            |
| `created_at`        | Upload timestamp            |

One user can upload multiple resumes.

```text
users 1 ---- many resumes
```

### Upload Workflow

1. Authenticate the user using JWT.
2. Read the uploaded file within the configured limit.
3. Validate the filename and extension.
4. Validate the PDF signature or DOCX structure.
5. Generate a SHA-256 checksum.
6. Generate a unique resume identifier and storage key.
7. Save the file using local storage or AWS S3.
8. Save the resume metadata in the database.
9. Return the public resume response.

### Error Responses

| Status | Meaning                                |
| ------ | -------------------------------------- |
| `201`  | Resume uploaded successfully           |
| `401`  | Authentication is required             |
| `413`  | File exceeds the configured size limit |
| `422`  | File format or structure is invalid    |
| `500`  | Resume metadata could not be persisted |
| `503`  | Storage backend is unavailable         |

### Database Migration

Day 4 introduces:

```text
20260803_0002_create_resumes
```

Apply and verify the migration from the `backend` directory:

```powershell
alembic upgrade head
alembic current
alembic history
alembic check
```

Expected current revision:

```text
20260803_0002 (head)
```

### Day 4 Verification

Run from the `backend` directory:

```powershell
ruff format app tests migrations
ruff check app tests migrations
ruff format --check app tests migrations
mypy app tests
pytest
```

The complete test suite must pass with at least 90% coverage.

### Documentation

Detailed resume storage documentation is available at:

```text
docs/resume-storage.md
```

## Day 5 — Resume Parsing Foundation

Day 5 adds deterministic PDF and DOCX resume parsing, OCR readiness detection, structured JSON generation, and persistent parse results.

### Implemented

- Parser interface and parser registry
- PDF text extraction with `pypdf`
- DOCX paragraph and table extraction with `python-docx`
- Password-protected and corrupt document handling
- Low-text detection for future OCR processing
- Structured extraction for contact information, summary, skills, education, experience, projects, and certifications
- Persistent raw text, structured JSON, parser metadata, and warnings
- Resume parse statuses: `pending`, `processing`, `completed`, `needs_ocr`, and `failed`
- JWT-protected parse and parsed-result endpoints
- Unit, service, API, storage-read, and migration tests

### Resume Parsing Endpoints

| Method | Endpoint                            | Description                       |
| ------ | ----------------------------------- | --------------------------------- |
| `POST` | `/api/v1/resume/{resume_id}/parse`  | Parse an uploaded resume          |
| `GET`  | `/api/v1/resume/{resume_id}/parsed` | Retrieve the stored parsed result |

### Current Migration

```text
20260803_0003_add_resume_parsing
```

### Dependencies

```text
pypdf==6.14.2
python-docx==1.2.0
```

### Verification

```powershell
ruff format app tests migrations
ruff check app tests migrations
ruff format --check app tests migrations
mypy app tests
alembic upgrade head
alembic current
alembic check
pytest
```

Detailed documentation:

```text
docs/resume-parsing.md
```

## Day 6 — Resume Parser API, Viewer, and History

Day 6 exposes the resume parser through a complete authenticated API and adds viewer, history, secure original-file access, and deletion workflows.

### Implemented

- Resume parsing status endpoint
- Paginated resume history ordered newest first
- Resume metadata endpoint
- Viewer-ready structured resume response
- Secure original PDF/DOCX download
- Local storage and AWS S3 file retrieval
- User ownership enforcement
- Resume deletion with parse-result cascade
- Physical file cleanup
- Compensating file restoration when database deletion fails
- Unit and integration tests

### Resume API Endpoints

| Method   | Endpoint                                  | Description                                      |
| -------- | ----------------------------------------- | ------------------------------------------------ |
| `GET`    | `/api/v1/resume/history`                  | List resume history with pagination              |
| `GET`    | `/api/v1/resume/{resume_id}`              | Retrieve resume metadata                         |
| `GET`    | `/api/v1/resume/{resume_id}/parse-status` | Retrieve current parse status                    |
| `GET`    | `/api/v1/resume/{resume_id}/viewer`       | Retrieve viewer-ready parsed content             |
| `GET`    | `/api/v1/resume/{resume_id}/file`         | Download the original private file               |
| `DELETE` | `/api/v1/resume/{resume_id}`              | Delete the resume, parse result, and stored file |

Existing parser endpoints remain:

| Method | Endpoint                            | Description                          |
| ------ | ----------------------------------- | ------------------------------------ |
| `POST` | `/api/v1/resume/{resume_id}/parse`  | Parse an uploaded resume             |
| `GET`  | `/api/v1/resume/{resume_id}/parsed` | Retrieve the persisted parsed result |

### Pagination

```text
GET /api/v1/resume/history?page=1&page_size=20
```

`page_size` accepts values from 1 to 100.

### Migration

Day 6 introduces no database migration. The current Alembic head remains:

```text
20260803_0003 (head)
```

Detailed documentation:

```text
docs/resume-api.md
```
