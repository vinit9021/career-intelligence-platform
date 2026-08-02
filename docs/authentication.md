# Authentication Architecture

## Scope

The authentication module provides:

- User registration
- User login
- Argon2 password hashing
- JWT access tokens
- JWT refresh tokens
- Refresh-token rotation
- Protected routes
- Active-account checks

## API Endpoints

### Register

POST /api/v1/auth/register

### Login

POST /api/v1/auth/login

### Refresh Token

POST /api/v1/auth/refresh

### Current User

GET /api/v1/auth/me

## Password Policy

Passwords must:

- Be between 12 and 128 characters
- Contain an uppercase letter
- Contain a lowercase letter
- Contain a digit
- Contain a special character
- Contain no whitespace

Passwords are stored only as Argon2 hashes.

## JWT Claims

Every token contains:

- sub: user identifier
- jti: unique token identifier
- type: access or refresh
- iat: issued-at time
- nbf: not-before time
- exp: expiration time
- iss: issuer
- aud: audience

Access and refresh tokens use separate signing secrets.

## Refresh-Token Rotation

When a refresh token is used:

1. Its signature and claims are validated.
2. Its SHA-256 hash is matched against storage.
3. The stored token is locked.
4. The old token is revoked.
5. A new access and refresh token pair is generated.
6. Reusing the old token is rejected.

## Day 2 Testing

Authentication integration tests use an isolated SQLite database.

Production PostgreSQL migration work remains part of the database milestone.