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
