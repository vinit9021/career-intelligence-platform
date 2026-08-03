# Resume Storage Architecture

## Day 4 Scope

Day 4 implements the resume upload and storage foundation for the Career Intelligence Platform.

### Implemented Features

- Secure resume upload
- PDF and DOCX file validation
- Configurable upload-size limit
- Local filesystem storage
- AWS S3 storage
- Storage-provider abstraction
- Resume metadata persistence
- SHA-256 file checksum generation
- Database rollback and file cleanup
- Unit and integration tests

Resume parsing, text extraction, ATS scoring, embeddings, and AI-agent processing are not included in Day 4.

---

## Resume Upload Endpoint

```text
POST /api/v1/resume/upload
```

The endpoint requires a valid JWT access token.

The request must use `multipart/form-data` with a file field named:

```text
file
```

---

## Supported File Formats

The application currently accepts:

- PDF (`.pdf`)
- DOCX (`.docx`)

The application validates both the filename extension and the internal file structure.

For PDF files, the uploaded content must begin with a valid PDF signature.

For DOCX files, the uploaded content must be a valid ZIP-based Office document containing the required DOCX files.

The API does not trust the MIME type supplied by the browser alone.

---

## Upload Size Limit

The default maximum resume size is 10 MB.

The limit is configured using:

```env
RESUME_MAX_SIZE_MB=10
```

Files larger than the configured limit are rejected with HTTP status `413`.

---

## Storage Abstraction

The application uses a common storage interface so the resume service does not depend directly on local storage or AWS S3.

Available storage backends:

- Local filesystem
- AWS S3

Select the active backend using:

```env
STORAGE_BACKEND=local
```

or:

```env
STORAGE_BACKEND=s3
```

Both storage implementations support:

- Saving files
- Deleting files
- Generated storage keys
- File-size metadata
- Storage ETag or checksum information

---

## Local Storage

Local storage is the default backend for development.

Configuration:

```env
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=storage
```

Uploaded files are stored inside:

```text
backend/storage/
```

The local storage directory must remain excluded from Git.

Resume files use generated storage keys in the following format:

```text
resumes/{user_id}/{resume_id}/original.{extension}
```

Generated keys prevent filename collisions and ensure that user-provided filenames are not used directly as filesystem paths.

---

## AWS S3 Storage

Enable AWS S3 using:

```env
STORAGE_BACKEND=s3
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your-private-resume-bucket
```

Optional configuration:

```env
AWS_S3_ENDPOINT_URL=
AWS_S3_KMS_KEY_ID=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
```

When explicit AWS credentials are not configured, Boto3 uses its standard AWS credential resolution chain.

This may include:

- Environment variables
- AWS credentials file
- AWS profile
- EC2 instance role
- ECS task role
- Other AWS-supported credential providers

The S3 bucket should remain private.

---

## S3 Encryption

Uploaded S3 objects use server-side encryption.

Default encryption:

```text
AES-256
```

When an AWS KMS key is configured:

```env
AWS_S3_KMS_KEY_ID=your-kms-key-id
```

the application uses AWS KMS server-side encryption.

---

## Storage Key Format

The backend generates a private storage key for every uploaded resume.

```text
resumes/{user_id}/{resume_id}/original.{extension}
```

The original uploaded filename is stored separately in the database.

The API response does not expose:

- Local filesystem paths
- S3 object keys
- AWS credentials
- Private bucket details

---

## Resume Database Model

Resume metadata is stored in the `resumes` table.

| Column              | Purpose                          |
| ------------------- | -------------------------------- |
| `id`                | Unique resume identifier         |
| `user_id`           | Identifier of the resume owner   |
| `original_filename` | Original uploaded filename       |
| `storage_backend`   | Selected storage backend         |
| `storage_key`       | Internal local or S3 storage key |
| `storage_etag`      | Storage ETag or checksum value   |
| `content_type`      | Validated content type           |
| `file_extension`    | Validated file extension         |
| `file_size_bytes`   | File size in bytes               |
| `sha256`            | SHA-256 file checksum            |
| `created_at`        | Resume upload timestamp          |

---

## Database Relationship

One user can upload multiple resumes.

```text
users 1 ---- many resumes
```

Each resume belongs to exactly one user.

Deleting a user also deletes the associated resume metadata through the configured cascade relationship.

Physical storage cleanup during user deletion can be introduced during a later lifecycle-management milestone.

---

## SHA-256 Checksum

Every uploaded resume receives a SHA-256 checksum.

The checksum is stored in:

```text
resumes.sha256
```

The checksum can later support:

- Duplicate-file detection
- File-integrity verification
- Audit logging
- Resume-version comparison
- Processing-cache identification

---

## Resume Upload Workflow

The resume upload process follows these steps:

1. Authenticate the user using JWT.
2. Read the uploaded file up to the configured size limit.
3. Verify that the file is not empty.
4. Sanitize and validate the filename.
5. Validate the file extension.
6. Validate the PDF signature or DOCX structure.
7. Generate a SHA-256 checksum.
8. Generate a unique resume identifier.
9. Generate a private storage key.
10. Save the file using local storage or AWS S3.
11. Save the resume metadata in the database.
12. Return the public resume response.

---

## Failure Handling

### Storage Failure

When file storage fails:

- Resume metadata is not committed.
- The API returns a storage-unavailable response.

### Database Failure

When database persistence fails after the file has been stored:

- The database transaction is rolled back.
- The newly stored file is deleted when possible.
- The API returns an internal server error.

This reduces the possibility of orphaned files.

---

## Successful API Response

A successful upload returns:

```text
201 Created
```

The response includes:

- Resume identifier
- Original filename
- Storage backend
- Content type
- File extension
- File size
- SHA-256 checksum
- Upload timestamp

---

## Error Responses

| Status | Meaning                                                                |
| ------ | ---------------------------------------------------------------------- |
| `201`  | Resume uploaded successfully                                           |
| `401`  | Authentication is required                                             |
| `413`  | File exceeds the configured size limit                                 |
| `422`  | File extension, MIME type, PDF signature, or DOCX structure is invalid |
| `500`  | Resume metadata could not be persisted                                 |
| `503`  | The configured storage backend is unavailable                          |

---

## Database Migration

Day 4 introduces the following migration:

```text
20260803_0002_create_resumes
```

It depends on:

```text
20260803_0001
```

Apply the migration from the `backend` directory:

```powershell
alembic upgrade head
```

Check the active migration:

```powershell
alembic current
```

Expected result:

```text
20260803_0002 (head)
```

Verify that SQLAlchemy models and Alembic migrations are synchronized:

```powershell
alembic check
```

---

## Environment Variables

Day 4 introduces the following environment variables:

```env
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=storage
RESUME_MAX_SIZE_MB=10

AWS_REGION=ap-south-1
AWS_S3_BUCKET=
AWS_S3_ENDPOINT_URL=
AWS_S3_KMS_KEY_ID=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
```

The private `.env` file must never be committed.

Only `.env.example` should be committed.

---

## Security Controls

The Day 4 implementation provides:

- JWT-protected uploads
- PDF and DOCX allow-list
- Upload-size restrictions
- PDF signature validation
- DOCX package validation
- Filename sanitization
- Path-traversal prevention
- Generated private storage keys
- SHA-256 checksums
- Private S3 object storage
- S3 server-side encryption
- Database rollback handling
- Stored-file cleanup after persistence failures
- No public exposure of internal storage keys

---

## Testing

Day 4 includes tests for:

- Resume model registration
- Resume database columns
- Database constraints
- User-to-resume relationship
- PDF validation
- DOCX validation
- Unsupported-file rejection
- Empty-file rejection
- Oversized-file rejection
- MIME-type mismatch rejection
- Local storage upload
- Local storage deletion
- Invalid storage-key rejection
- S3 upload
- S3 deletion
- S3 AES-256 encryption
- S3 KMS encryption
- S3 error handling
- Storage factory selection
- Resume metadata persistence
- Storage failure handling
- Database failure cleanup
- Authenticated resume upload
- Unauthenticated upload rejection
- Migration verification

---

## Day 4 Non-Scope

The following features are intentionally deferred:

- Resume text extraction
- PDF text parsing
- DOCX text parsing
- Resume section detection
- ATS scoring
- Resume quality analysis
- Embedding generation
- FAISS indexing
- Resume optimization
- LangGraph workflows
- Resume version management
- Resume download endpoint
- Resume listing endpoint
- Resume deletion endpoint
