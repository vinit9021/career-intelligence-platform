# Career Intelligence Platform Architecture

## Purpose

Career Intelligence Platform is an AI-powered job-search operating system that
manages resume intelligence, job analysis, application tracking, recruiter
communication, online-assessment preparation, interview preparation, and
career analytics.

The platform will use specialized AI agents coordinated through LangGraph while
persisting important application state in PostgreSQL.

## High-Level Architecture

```text
Next.js Frontend
        |
        | HTTPS / JSON
        v
FastAPI Backend
        |
        +-- API Layer
        +-- Application Services
        +-- Repository Layer
        +-- AI Agents
        +-- LangGraph Workflows
        +-- Background Workers
        |
        +-- PostgreSQL
        +-- Redis
        +-- FAISS
        +-- AWS S3
        +-- Gmail API
```

## Backend Architecture

```text
HTTP Request
      |
      v
FastAPI Router
      |
      v
Pydantic Request Schema
      |
      v
Application Service
      |
      +-------------------+
      |                   |
      v                   v
Repository             External Tool
      |                   |
      v                   v
PostgreSQL          S3 / Gmail / AI APIs
```

### API Layer

The API layer:

- Receives HTTP requests.
- Validates request data.
- Invokes application services.
- Converts application results into API responses.
- Returns structured errors.

Location:

```text
backend/app/api/
```

### Schema Layer

The schema layer contains Pydantic models for:

- API requests.
- API responses.
- Agent inputs.
- Agent outputs.
- Workflow state.

Location:

```text
backend/app/schemas/
```

### Service Layer

The service layer contains application use cases.

Responsibilities include:

- Coordinating repositories.
- Calling external integrations.
- Applying application rules.
- Managing transactions.
- Keeping API handlers small.

Location:

```text
backend/app/services/
```

### Repository Layer

The repository layer isolates database access from application logic.

Responsibilities include:

- Creating records.
- Reading records.
- Updating records.
- Deleting records.
- Executing database queries.

Location:

```text
backend/app/repositories/
```

### Model Layer

The model layer will contain SQLAlchemy database models and relationships.

Location:

```text
backend/app/models/
```

### Agent Layer

Each AI agent will have one clearly defined responsibility.

Every agent will define:

- Purpose.
- Structured input.
- Structured output.
- Prompt.
- Tools.
- Retry strategy.
- Failure handling.
- Logging.
- Testing strategy.

Location:

```text
backend/app/agents/
```

### Workflow Layer

LangGraph workflows will coordinate multiple agents and human approval steps.

Location:

```text
backend/app/workflows/
```

### Tool Layer

The tool layer will isolate integrations such as:

- Gmail API.
- AWS S3.
- Document extraction.
- Embedding generation.
- Vector search.
- Company research.
- Calendar integration.

Location:

```text
backend/app/tools/
```

### Prompt Layer

Prompts will be stored separately from agent implementation code to support
versioning, testing, and prompt regression checks.

Location:

```text
backend/app/prompts/
```

### Database Layer

Database configuration, sessions, migrations, and base classes will be stored
inside:

```text
backend/app/db/
```

## Frontend Architecture

```text
Next.js App Router
        |
        v
Pages and Layouts
        |
        v
Reusable Components
        |
        v
React Query Hooks
        |
        v
Typed API Client
        |
        v
FastAPI Backend
```

The frontend will use:

- Next.js App Router.
- TypeScript.
- Tailwind CSS.
- TanStack React Query.
- Reusable components.
- Responsive SaaS-style layouts.
- Environment-based API configuration.

## Planned Infrastructure

The completed platform will use:

- PostgreSQL for persistent relational data.
- Redis for caching and background-job coordination.
- FAISS for vector similarity search.
- AWS S3 for uploaded resumes and attachments.
- Docker for repeatable local and production environments.
- Background workers for email synchronization and long-running jobs.
- OpenTelemetry and Grafana for observability.

## API Versioning

All current API endpoints use the version-one prefix:

```text
/api/v1
```

Current endpoint:

```text
GET /api/v1/health
```

Future modules will be registered through the versioned API router without
changing the FastAPI application entry point.

## Current Day 1 Implementation

Implemented:

- Monorepo foundation.
- Backend and frontend separation.
- Python virtual environment.
- FastAPI application factory.
- Versioned API routing.
- Health endpoint.
- Pydantic response schema.
- Typed environment configuration.
- Centralized logging configuration.
- CORS configuration.
- Backend linting and formatting.
- Backend static type checking.
- Backend API testing.
- Test coverage enforcement.
- Next.js App Router.
- TypeScript.
- Tailwind CSS.
- TanStack React Query provider.
- Frontend environment configuration.
- ESLint.
- Prettier.
- Frontend production build verification.

## Not Yet Implemented

The following modules belong to future milestones:

- Authentication.
- JWT access and refresh tokens.
- User and profile database models.
- SQLAlchemy.
- Alembic.
- PostgreSQL connection.
- Resume upload.
- AWS S3 integration.
- Resume parsing.
- Job-description analysis.
- ATS optimization.
- LangGraph orchestration.
- Gmail synchronization.
- Redis.
- Background workers.
- FAISS.
- Dashboard modules.
- Analytics.
- Notifications.
- Docker configuration.
- CI/CD.
- Production deployment.

## Current Repository Structure

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
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/
│       ├── lib/
│       └── providers/
├── docker/
├── docs/
├── infra/
└── README.md
```

## Next Milestone

Week 1, Day 2 will implement the authentication architecture, including:

- User registration.
- Login.
- Password hashing.
- JWT access tokens.
- Refresh tokens.
- Protected routes.
- Authentication validation.
- Authentication error responses.
- Unit and integration tests.