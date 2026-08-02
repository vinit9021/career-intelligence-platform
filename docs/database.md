# Database Architecture

## Technology

The backend uses PostgreSQL with SQLAlchemy async sessions and asyncpg.

Alembic manages all production schema migrations.

## Current Tables

### users

Stores authentication and account information.

Important fields:

- id
- email
- password_hash
- full_name
- is_active
- is_verified
- created_at
- updated_at

### profiles

Stores career-profile information associated with one user.

Important fields:

- headline
- location
- phone
- bio
- years_experience
- target_roles
- skills
- linkedin_url
- github_url
- portfolio_url

A user can have at most one profile.

Deleting a user deletes the related profile automatically.

### refresh_tokens

Stores hashed refresh-token records for secure token rotation.

Deleting a user deletes all related refresh-token records.

## Repository Layer

UserRepository handles user persistence operations.

ProfileRepository handles profile persistence operations.

Business rules remain in UserService rather than being placed inside API routes.

## User API

GET /api/v1/users/me

PATCH /api/v1/users/me

DELETE /api/v1/users/me

## Profile API

POST /api/v1/users/me/profile

GET /api/v1/users/me/profile

PATCH /api/v1/users/me/profile

DELETE /api/v1/users/me/profile

## Migration Commands

Apply migrations:

alembic upgrade head

Show current migration:

alembic current

Show migration history:

alembic history

Check model and database consistency:

alembic check

Rollback one migration:

alembic downgrade -1