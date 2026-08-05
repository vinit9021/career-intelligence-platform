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

## Day 5 — Resume Parser AI Agent

Day 5 implements an Agentic AI–based resume parsing workflow using LangChain, LangGraph, and the Groq LLM API.

### Objective

Convert uploaded PDF and DOCX resumes into validated, structured JSON while ensuring that the system does not invent information that is absent from the original resume.

### Complete Workflow

```text
User uploads PDF/DOCX resume
        ↓
File validation
        ↓
Secure local or AWS S3 storage
        ↓
PDF/DOCX text extraction
        ↓
Deterministic baseline parser
        ↓
LangGraph Resume Parser workflow
        ↓
LangChain + Groq Resume Parser Agent
        ↓
Pydantic structured output
        ↓
Factuality validation
        ↓
Valid / Retry / OCR Required / Fallback
        ↓
Structured resume result
        ↓
PostgreSQL persistence
```

### Resume Parser AI Agent

The Resume Parser Agent semantically understands the extracted resume text and organizes it into structured sections.

It extracts:

- Contact information
- Professional summary
- Technical and professional skills
- Work experience
- Education
- Projects
- Certifications
- Achievements
- Languages
- Professional links
- Additional resume sections

The agent uses Groq through LangChain and returns its response using the existing Pydantic resume schema instead of returning unstructured text.

### Agentic Architecture

The Resume Parser Agent is implemented using the following components:

```text
LangChain
    ↓
Prompt construction and structured LLM output

Groq Chat Model
    ↓
Semantic understanding of resume content

LangGraph
    ↓
Workflow state, routing, retries and fallback

Pydantic
    ↓
Structured and validated resume output

Deterministic Validator
    ↓
Factuality and evidence checks
```

### LangGraph Workflow State

The workflow maintains a shared state containing:

```text
resume_text
baseline_result
agent_result
final_result
attempt_count
max_attempts
validation_errors
warnings
requires_ocr
workflow_status
last_error
```

Supported workflow statuses include:

```text
pending
assessing_text
analyzing
validating
retrying
completed
completed_with_fallback
needs_ocr
failed
```

### Workflow Nodes

#### 1. Text Assessment Node

Checks whether the extracted resume text is meaningful and sufficiently long.

When the extracted text is too short or unusable, the resume is marked as:

```text
needs_ocr
```

#### 2. Resume Analysis Node

Sends the following information to the Groq Resume Parser Agent:

- Original extracted resume text
- Deterministic baseline result
- Resume parsing system prompt
- Validation feedback from previous attempts
- Required Pydantic output schema

#### 3. Validation Node

Validates the structured result returned by the AI agent.

The validator checks:

- Whether meaningful resume content was returned
- Whether extracted email addresses exist in the source resume
- Whether extracted phone numbers exist in the source resume
- Whether extracted skills have supporting evidence
- Whether the output follows the required Pydantic schema
- Whether unsupported information was generated

#### 4. Retry Route

When validation fails and attempts remain, LangGraph sends the validation errors back to the Resume Parser Agent.

```text
Agent output
    ↓
Validation failed
    ↓
Validation feedback added to state
    ↓
Agent runs again
    ↓
Corrected structured output
```

#### 5. Deterministic Fallback Route

When Groq is unavailable or the retry limit is exhausted, the workflow uses the deterministic parser result as a controlled fallback.

The result is marked as:

```text
completed_with_fallback
```

A warning is included to indicate that AI parsing was unavailable or invalid.

#### 6. OCR Route

When a PDF contains scanned images and does not provide sufficient extractable text, the workflow returns:

```text
requires_ocr = true
status = needs_ocr
```

Full OCR processing will be implemented separately.

### Agent Guardrails

The Resume Parser Agent is instructed to:

- Use only information explicitly present in the source resume
- Never invent skills, employers, roles, dates, degrees or achievements
- Never invent measurable results or experience
- Preserve organization names and technology names accurately
- Preserve email addresses, phone numbers and URLs accurately
- Keep dates in their original form when uncertain
- Return empty values when information is unavailable
- Separate experience, education, projects and certifications correctly
- Correct earlier mistakes using validator feedback
- Return only structured output matching the required schema

### Existing Day 5 Components

The earlier deterministic Day 5 implementation remains in the project because it provides tools and infrastructure required by the AI agent.

Existing components are used for:

- PDF text extraction
- DOCX text extraction
- File validation
- Secure resume storage
- Deterministic baseline generation
- AI-agent fallback behavior
- Database persistence
- Resume history
- API integration
- Result validation

The deterministic parser is no longer intended to be the main intelligence layer. It acts as an agent tool, baseline generator, validator and fallback.

### Groq Configuration

The project uses Groq instead of the OpenAI API.

Required private `.env` configuration:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-private-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
AGENT_TIMEOUT_SECONDS=60
AGENT_MODEL_MAX_RETRIES=2
```

The real Groq API key is stored only in the private `.env` file and must never be committed to GitHub.

The public `.env.example` contains only placeholders:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=replace-with-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
AGENT_TIMEOUT_SECONDS=60
AGENT_MODEL_MAX_RETRIES=2
```

### Main Agentic Files

```text
backend/app/agents/base/errors.py
backend/app/agents/resume_parser/agent.py
backend/app/agents/resume_parser/state.py
backend/app/agents/resume_parser/validator.py
backend/app/llm/factory.py
backend/app/prompts/resume_parser.py
backend/app/workflows/resume_parser.py
backend/tests/agents/test_resume_parser_agent.py
backend/tests/workflows/test_resume_parser_workflow.py
backend/requirements-agentic.txt
```

### Technology Stack

- Python
- FastAPI
- LangChain
- LangGraph
- Groq API
- ChatGroq
- Pydantic
- PostgreSQL
- SQLAlchemy
- PDF text extraction
- DOCX text extraction
- Local storage
- AWS S3 storage abstraction
- Pytest
- Ruff
- MyPy

### Testing

Automated Day 5 agent tests use mocked LangChain runnables and do not make real paid API calls.

Implemented tests cover:

- Resume Parser Agent input preparation
- Prompt factuality instructions
- Successful structured resume generation
- LangGraph workflow execution
- Retry after a temporary model failure
- OCR routing for insufficient text
- Structured-output validation
- Workflow status transitions

The focused agent and workflow tests pass successfully.

### Day 5 Status

Completed:

- Groq LLM factory
- LangChain Resume Parser Agent
- Dedicated resume parsing prompt
- Pydantic structured output
- LangGraph workflow state
- Text-quality assessment
- AI resume analysis node
- Factuality validation
- Conditional retry routing
- OCR-required routing
- Deterministic fallback
- Mocked agent tests
- Mocked LangGraph workflow tests

Remaining before Day 5 is fully complete:

- Connect the existing PDF/DOCX extraction service to the LangGraph workflow
- Update the existing resume parsing service and API to invoke the AI agent
- Persist the final AI-agent result using the existing repository
- Add API-to-agent integration tests
- Add database persistence integration tests
- Run the complete project test suite
- Confirm project coverage remains at least 90%

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

## Day 7 — Phase 1 Stabilization and Quality Gate

Day 7 closes Phase 1 by validating the complete Authentication and Resume Parsing foundation.

### Completed

- Full authentication, profile, resume upload, parsing, viewer, history, file retrieval, and deletion regression coverage
- Phase 1 OpenAPI contract verification
- Private file-response security headers
- Repository audit for tracked secrets and generated files
- Verification of ignored `.env` and local resume storage
- Consolidated Phase 1 completion documentation
- One-command quality gate for Ruff, MyPy, Alembic, Pytest, and repository auditing

### Phase 1 Verification

Run from the project root:

```powershell
.\scripts\verify-phase1.ps1
```

The quality gate verifies:

- Ruff formatting and linting
- MyPy strict typing
- Alembic head and migration synchronization
- Complete Pytest suite with the configured coverage threshold
- Required Phase 1 API operations
- Required Phase 1 documentation
- No tracked private `.env`, uploaded resumes, caches, local databases, or credential files
- No obvious committed secrets in tracked text files

### Phase 1 Capabilities

- JWT authentication and refresh-token rotation
- Authenticated user and profile CRUD
- PostgreSQL persistence and Alembic migrations
- PDF and DOCX resume uploads
- Local and AWS S3 storage backends
- Resume parsing and structured JSON extraction
- OCR-readiness status
- Resume viewer and parsing status APIs
- Resume history and pagination
- Secure private file retrieval
- Resume deletion with storage cleanup

Detailed completion documentation:

```text
docs/phase1-completion.md
```

## Day 8 — Job Description Parser

Day 8 adds a deterministic parser that converts pasted job-description text into structured Pydantic JSON.

### Implemented

- Job-description text normalization
- Empty and oversized input validation
- Unsafe control-character removal
- Job-title extraction
- Company-name extraction when present
- Required-skill extraction
- Preferred-skill extraction
- Technology and tool extraction
- Responsibility extraction
- Qualification extraction
- Experience requirement extraction
- Education requirement extraction
- Seniority classification
- ATS keyword extraction
- Parser warnings and metadata
- Unit and schema tests

### Structured Output

The parser returns:

```text
job_title
company_name
required_skills
preferred_skills
technologies
responsibilities
qualifications
experience
education_requirements
seniority_level
ats_keywords
normalized_text
metadata
```

### Usage

```python
from app.parsers import JobDescriptionParser

parser = JobDescriptionParser()
result = parser.parse(job_description_text)
payload = result.model_dump(mode="json")
```

### Day 8 Non-Scope

- Job-description API
- Database persistence
- Job-description history
- Resume matching
- ATS scoring
- Resume optimization
- Embeddings or FAISS
- LangGraph orchestration

Detailed documentation:

```text
docs/job-description-parser.md
```

## Day 9 — Resume Matching Engine

Day 9 adds a deterministic and explainable engine that compares parsed resume data with parsed job-description data.

### Implemented

- Required-skill matching
- Preferred-skill matching
- Technology and tool matching
- ATS-keyword matching
- Alias normalization
- Experience comparison
- Education comparison
- Responsibility alignment
- Resume evidence extraction
- Weighted overall match score
- Strength and weakness explanations
- Category-level scoring breakdown
- Deterministic-output tests

### Scoring Categories

```text
Required skills
Preferred skills
Technologies
ATS keywords
Experience
Education
Responsibilities
```

Categories that are not specified in the job description are excluded and their weights are redistributed across applicable categories.

### Usage

```python
from app.matching import match_resume_to_job

result = match_resume_to_job(
    resume=parsed_resume.content,
    job_description=parsed_job_description,
    resume_raw_text=parsed_resume.raw_text,
)
```

### Day 9 Non-Scope

- Matching API
- Database persistence
- ATS rewriting
- Resume optimization
- Resume version creation
- Embeddings or FAISS
- LLM calls
- LangGraph orchestration

Detailed documentation:

```text
docs/resume-matching-engine.md
```
