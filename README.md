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

## Day 8 — Job Description Analyzer AI Agent

Day 8 upgrades the original deterministic Job Description Parser into an Agentic AI workflow using LangChain, LangGraph, Groq, Pydantic structured output, evidence validation, conditional retries, and controlled fallback behavior.

### Objective

Semantically analyze raw job descriptions and convert them into validated structured data that can be used by the Resume Matching Agent, ATS Optimization Agent, Company Research Agent, Skill Gap Agent, and application-tracking workflows.

### Complete Workflow

```text
Raw Job Description
        ↓
Text Normalization
        ↓
Deterministic Baseline Parser
        ↓
LangGraph Job Description Analyzer Workflow
        ↓
LangChain + Groq Job Description Analyzer Agent
        ↓
Pydantic Structured Output
        ↓
Evidence and Hallucination Validation
        ↓
Valid Result / Retry / Deterministic Fallback
        ↓
Structured Job Description Analysis
```

### Job Description Analyzer AI Agent

The Job Description Analyzer Agent semantically understands natural-language job descriptions and extracts:

- Job title
- Company name
- Required skills
- Preferred skills
- Technologies and tools
- Responsibilities
- Qualifications
- Minimum and maximum experience requirements
- Education requirements
- Seniority level
- ATS keywords
- Normalized job-description text
- Warnings and analysis metadata

Unlike the original deterministic parser, the AI agent can understand different recruiting sentence structures such as:

```text
We Dolat Capital are looking for a Software Engineer.
Join Dolat Capital as a Backend Developer.
Dolat Capital seeks an experienced Python Engineer.
At Dolat Capital, you will develop backend services.
Our engineering team is hiring a FastAPI developer.
```

### Agentic Architecture

```text
LangChain
    ↓
Prompt construction and structured LLM invocation

Groq Chat Model
    ↓
Semantic understanding of job-description content

LangGraph
    ↓
Workflow state, nodes, routing, retries and fallback

Pydantic
    ↓
Validated structured job-description output

Deterministic Validator
    ↓
Evidence checks and hallucination detection
```

### LangGraph Workflow State

The workflow maintains shared state containing:

```text
job_description_text
normalized_text
baseline_result
agent_result
final_result
attempt_count
max_attempts
validation_errors
warnings
status
last_error
```

Supported workflow statuses:

```text
pending
normalizing
baselining
analyzing
validating
retrying
completed
completed_with_fallback
failed
```

### Workflow Nodes

#### 1. Input Normalization Node

The input normalization node:

- Normalizes line endings
- Removes unnecessary blank lines
- Trims extra whitespace
- Preserves meaningful job-description sections
- Rejects descriptions that are too short for useful analysis

A short invalid description is rejected before making a Groq API request.

#### 2. Deterministic Baseline Node

The original Day 8 parser runs first and produces baseline information such as:

- Initial job title
- Initial company name
- Detected skills
- Detected technologies
- Responsibilities
- Experience requirements
- Education requirements
- ATS keywords

The deterministic result is provided to the AI agent as supporting evidence. It is not treated as the final intelligence output.

#### 3. Groq AI Analysis Node

LangChain sends the following information to the Groq Job Description Analyzer Agent:

- Original normalized job description
- Deterministic baseline result
- Dedicated system prompt
- Validation feedback from earlier attempts
- Required Pydantic output schema

The Groq model semantically understands the description and returns a structured `ParsedJobDescription` object.

#### 4. Evidence Validation Node

The validator checks the AI-generated result against the original job description.

Validation includes:

- Checking that meaningful information was returned
- Verifying that the company name appears in the source text
- Checking whether the job title is supported by source terms
- Verifying required skills
- Verifying preferred skills
- Verifying technologies
- Verifying ATS keywords
- Checking responsibility alignment
- Detecting unsupported or fabricated information

Important unsupported fields, such as an invented company name, cause validation failure.

Less critical uncertain fields are added as warnings for evidence review.

#### 5. Conditional Retry Route

When the agent output fails validation and retries remain, LangGraph sends the validation feedback back to the agent.

```text
Groq Agent Output
        ↓
Validation Failure
        ↓
Validation Errors Added to LangGraph State
        ↓
Agent Runs Again with Correction Instructions
        ↓
Corrected Structured Output
```

The workflow prevents infinite retries by enforcing a maximum attempt count.

#### 6. Deterministic Fallback Route

When Groq is unavailable, the API key is invalid, the request fails, or the AI output remains invalid after all retries, the workflow uses the original deterministic parser result.

The final status becomes:

```text
completed_with_fallback
```

The output includes the warning:

```text
AI job-description analysis was unavailable or invalid.
The deterministic parser result was used.
```

This ensures that the platform continues working even when the AI provider is temporarily unavailable.

### Agent Guardrails

The Job Description Analyzer Agent is instructed to:

- Use only information supported by the source job description
- Never invent a company name
- Never invent a job title
- Never invent required or preferred skills
- Never invent technologies or tools
- Never invent responsibilities
- Never invent qualifications
- Never invent education requirements
- Never invent experience requirements
- Never convert preferred requirements into required requirements
- Preserve company names, job titles, technologies, degrees, numbers, and experience ranges accurately
- Return empty values when information is unavailable
- Correct mistakes using validation feedback
- Return only structured output matching the required Pydantic schema

### Existing Deterministic Day 8 Parser

The original deterministic parser remains in the project as:

- A preprocessing tool
- A baseline generator
- Supporting evidence for the AI agent
- A validation reference
- A controlled fallback
- A regression-testing baseline

The deterministic parser is no longer intended to be the main intelligence layer.

### Main Agentic Files

```text
backend/app/agents/job_description_analyzer/__init__.py
backend/app/agents/job_description_analyzer/agent.py
backend/app/agents/job_description_analyzer/state.py
backend/app/agents/job_description_analyzer/validator.py
backend/app/prompts/job_description_analyzer.py
backend/app/workflows/job_description_analyzer.py
backend/tests/agents/test_job_description_analyzer_agent.py
backend/tests/workflows/test_job_description_analyzer_workflow.py
```

### Existing Supporting Files

```text
backend/app/parsers/job_description.py
backend/app/schemas/job_description_parser.py
backend/tests/unit/test_job_description_parser.py
backend/tests/unit/test_job_description_schema.py
```

### Groq Configuration

The Job Description Analyzer Agent reuses the shared Groq configuration:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-private-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
AGENT_TIMEOUT_SECONDS=60
AGENT_MODEL_MAX_RETRIES=2
```

The real Groq API key is stored only inside the private `.env` file and must never be committed to GitHub.

The public `.env.example` contains only placeholders.

### Technology Stack

- Python
- FastAPI
- LangChain
- LangGraph
- Groq API
- ChatGroq
- Pydantic structured output
- Deterministic parsing tools
- Evidence validation
- Pytest
- Ruff
- MyPy

### Testing

Corrected Day 8 includes tests for:

- Agent prompt-payload preparation
- Anti-hallucination prompt rules
- Fake company-name rejection
- Successful AI workflow execution
- Company extraction from natural recruiting language
- Retry after invalid AI output
- Controlled fallback after Groq failure
- Short-input rejection
- Existing deterministic parser regression
- Existing Pydantic schema validation

Automated tests use mocked LangChain runnables and do not make real Groq API calls.

### Day 8 Status

Completed:

- LangChain Job Description Analyzer Agent
- Dedicated job-description analyzer prompt
- Groq structured-output integration
- LangGraph workflow state
- Input normalization node
- Deterministic baseline node
- Groq analysis node
- Evidence-validation node
- Conditional retry routing
- Deterministic fallback routing
- Workflow tests
- Agent tests
- Existing parser regression tests

Future integration:

- Add a production API or service entry point for the agent workflow
- Persist analyzed job descriptions when job and application storage is introduced
- Connect the structured result to the Resume Matching Agent
- Include the analyzer inside the complete multi-agent LangGraph workflow

## Day 9 — Resume Matching AI Agent

Day 9 upgrades the deterministic matching engine into a hybrid AI-powered Resume Matching Agent using LangChain, LangGraph, Groq, and Pydantic.

### Features

- Required and preferred skill matching
- Technology and ATS keyword matching
- Semantic requirement comparison
- Responsibility alignment
- Resume evidence validation
- Hybrid match scoring
- Retry handling for invalid AI output
- Deterministic fallback when Groq is unavailable

### Main Files

```text
backend/app/agents/resume_matching/
backend/app/prompts/resume_matching.py
backend/app/workflows/resume_matching.py
backend/tests/agents/test_resume_matching_agent.py
backend/tests/workflows/test_resume_matching_workflow.py
```

### Status

- Resume Matching AI Agent implemented
- Semantic evidence validation added
- Hybrid deterministic + AI scoring added
- LangGraph retry and fallback added
- 21 focused tests passed

## Day 10 — ATS Optimization AI Agent

Day 10 adds an ATS Optimization Agent using LangChain, LangGraph, Groq, Pydantic, and deterministic fallback logic.

### Features

- ATS baseline score
- Keyword coverage and missing keyword detection
- Safe and conditional keyword recommendations
- Summary improvement suggestions
- Experience and project bullet rewrites
- Section-wise ATS recommendations
- Fabricated skill and metric validation
- Retry handling and deterministic fallback

### Main Files

```text
backend/app/agents/ats_optimization/
backend/app/ats/
backend/app/prompts/ats_optimization.py
backend/app/workflows/ats_optimization.py
backend/tests/agents/test_ats_optimization_agent.py
backend/tests/unit/test_ats_optimizer.py
backend/tests/workflows/test_ats_optimization_workflow.py
```

### Status

- ATS Optimization AI Agent implemented
- Groq structured output integrated
- Evidence validation added
- LangGraph retry and fallback added
- Day 10 tests added

## Day 11 — Resume Version Manager

Day 11 adds a Resume Version Manager to maintain multiple resume variants and track their complete version history.

### Features

- Backend, AI, ML, and Full-stack resume variants
- Automatic version numbering
- Active resume version management
- Resume version history
- ATS score and optimization snapshot storage
- Track which resume version was submitted for an application
- PostgreSQL persistence with Alembic migration
- LangGraph-based version management workflow

### Main Files

```text
backend/app/models/resume_version.py
backend/app/schemas/resume_version.py
backend/app/repositories/resume_versions.py
backend/app/services/resume_versions.py
backend/app/agents/resume_version_manager/
backend/app/workflows/resume_version_manager.py
```

## Day 12 — Cover Letter AI Agent

Day 12 adds a personalized Cover Letter Agent using LangChain, LangGraph, Groq, and evidence-based validation.

### Features

- Personalized role and company-specific cover letters
- Resume and job-description based generation
- Resume evidence validation
- Unsupported skill and fabricated metric detection
- Configurable tone and word limit
- Retry handling for invalid AI output
- Deterministic fallback when Groq is unavailable

### Main Files

```text
backend/app/agents/cover_letter/
backend/app/cover_letters/
backend/app/prompts/cover_letter.py
backend/app/workflows/cover_letter.py
backend/tests/agents/test_cover_letter_agent.py
backend/tests/unit/test_cover_letter_generator.py
backend/tests/workflows/test_cover_letter_workflow.py
```

## Day 13 — Skill Gap AI Agent

Day 13 adds a Skill Gap Agent using LangChain, LangGraph, Groq, and deterministic skill-gap analysis.

### Features

- Required and preferred skill-gap detection
- Technology gap identification
- Gap priority classification
- Personalized learning roadmap
- Practical exercises and mini-project recommendations
- False skill-gap validation
- LangGraph retry handling
- Deterministic fallback when Groq is unavailable

### Main Files

```text
backend/app/agents/skill_gap/
backend/app/skill_gap/
backend/app/prompts/skill_gap.py
backend/app/workflows/skill_gap.py
backend/tests/agents/test_skill_gap_agent.py
backend/tests/unit/test_skill_gap_analyzer.py
backend/tests/workflows/test_skill_gap_workflow.py
```
