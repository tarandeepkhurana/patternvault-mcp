# Supabase Setup

This repo uses Supabase for Auth, Postgres, pgvector-backed retrieval, and Storage. The reusable pattern is: frontend uses public Supabase Auth values, backend verifies tokens and uses server-only database/storage credentials, and Postgres remains the source of truth.

## Runtime Responsibilities

```text
Frontend
  -> Supabase Auth with public anon key
  -> sends access token to backend

Backend
  -> verifies token with Supabase Auth API
  -> uses async SQLAlchemy for Postgres
  -> uses service role key for Storage server operations
  -> enforces user_id boundaries in DB queries

Postgres
  -> durable app state
  -> pgvector embeddings
  -> full-text search

Supabase Storage
  -> uploaded PDFs and previews
```

## Backend Environment Variables

These live in the root `.env` and are loaded by `src/config.py`.

```text
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe

DATABASE_URL=
DIRECT_URL=
ALEMBIC_URL=

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_RESUME_BUCKET=resumes

MESSAGE_HISTORY_LIMIT=8
```

## Supabase Dashboard Values To Env Mapping

Use this mapping when setting up a new project from the Supabase dashboard:

```text
Supabase Project URL
  -> backend SUPABASE_URL
  -> frontend VITE_SUPABASE_URL

Supabase anon/public key
  -> frontend VITE_SUPABASE_ANON_KEY
  -> backend does not need it in this repo

Supabase service_role key
  -> backend SUPABASE_SERVICE_ROLE_KEY
  -> never frontend

Supabase transaction pooler or pooled connection string
  -> backend DATABASE_URL, if using it for read/runtime traffic

Supabase direct/session connection string
  -> backend DIRECT_URL, if using it for write/runtime traffic
  -> backend ALEMBIC_URL, with a sync driver, for migrations

Database password
  -> embedded inside DATABASE_URL, DIRECT_URL, and ALEMBIC_URL
  -> do not expose separately unless tooling requires it

JWT secret
  -> not used by this repo
  -> only needed if verifying JWTs locally instead of calling Auth API

Supabase access token
  -> not app runtime
  -> only for CLI/admin automation
```

### `SUPABASE_URL`

Purpose:

- Public project URL, for example the base URL shown in Supabase project settings.
- Used by backend for Auth API and Storage API calls.
- Safe to give to frontend as `VITE_SUPABASE_URL`.

Used in:

- `src/auth/dependencies.py`
- `src/services/resume/resume_storage.py`

### `SUPABASE_SERVICE_ROLE_KEY`

Purpose:

- Backend-only privileged key.
- Used here to verify users through Supabase Auth API and to upload/sign storage objects.
- Bypasses RLS when used directly against Supabase APIs, so the backend must enforce user boundaries.

Never give this to frontend.

Used in:

- `src/auth/dependencies.py`
- `src/services/resume/resume_storage.py`

### `SUPABASE_RESUME_BUCKET`

Purpose:

- Storage bucket name for uploaded artifacts.
- Defaults to `resumes`.

Reusable adaptation:

- Rename to `SUPABASE_ARTIFACT_BUCKET`, `SUPABASE_DOCUMENT_BUCKET`, or capability-specific names in new projects.

### `DATABASE_URL`

Purpose in this repo:

- Async SQLAlchemy URL for the read engine.
- Used by `read_engine` in `src/db/client.py`.
- Commonly points to Supabase pooler when running app queries.

Expected shape:

```text
postgresql+asyncpg://...
```

Important:

- If using Supabase transaction pooler/PgBouncer, keep `statement_cache_size: 0` in asyncpg connect args.
- Do not expose this URL to frontend.

### `DIRECT_URL`

Purpose in this repo:

- Async SQLAlchemy URL for the write engine.
- Used by `write_engine` in `src/db/client.py`.
- Can point to a direct connection or a session-pooler connection depending on Supabase setup.

Expected shape:

```text
postgresql+asyncpg://...
```

Important:

- This is backend-only.
- The repo currently applies the same PgBouncer-safe connect args to both read and write engines.

### `ALEMBIC_URL`

Purpose:

- Sync SQLAlchemy URL for Alembic migrations.
- Used only by `src/db/migrations/env.py`.

Expected shape:

```text
postgresql://...
postgresql+psycopg://...
```

Important:

- Do not use `postgresql+asyncpg://` for Alembic.
- Prefer a direct/session connection for migrations.
- Do not expose this URL to frontend.

### `OPENAI_API_KEY`

Purpose:

- Backend-only provider key for LLM, embedding, and transcription calls.

Used in:

- `src/factories/llm_factory.py`
- `src/factories/embedding_factory.py`
- `src/services/voice/transcription_service.py`

Never give this to frontend.

## Frontend Environment Variables

These live in `src/frontend/.env`.

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

### `VITE_API_BASE_URL`

Purpose:

- Backend API base URL.
- Used by frontend fetch calls.

### `VITE_SUPABASE_URL`

Purpose:

- Same value as backend `SUPABASE_URL`.
- Safe public project URL.

### `VITE_SUPABASE_ANON_KEY`

Purpose:

- Supabase public anon key for browser Auth.
- Used to sign up, sign in, refresh sessions, and sign out.

Safe to expose in frontend, assuming Supabase Auth/RLS/backend checks are configured correctly.

## Keys Not Given To Frontend

Never provide these to frontend:

```text
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
DIRECT_URL
ALEMBIC_URL
OPENAI_API_KEY
SUPABASE_ACCESS_TOKEN
SUPABASE_DB_PASSWORD
SUPABASE_JWT_SECRET
```

Notes:

- `SUPABASE_JWT_SECRET` is only needed if the backend verifies JWTs locally. This repo does not; it calls Supabase Auth API.
- `SUPABASE_ACCESS_TOKEN` is for Supabase CLI/admin automation, not app runtime.
- Storage S3 access keys are not used in this repo because Storage is accessed through Supabase REST endpoints with the service role key.

## Database Setup

Recommended Supabase setup:

1. Create a Supabase project.
2. Enable the `vector` extension for pgvector.
3. Create storage bucket `resumes` or your configured bucket name.
4. Set backend `.env` values.
5. Run Alembic migrations:

```powershell
alembic upgrade head
```

6. If using manual FTS triggers during prototype, run the SQL from `docs/models.md` in Supabase SQL editor. In production, prefer migrating triggers/functions through Alembic.

## Current DB Structure

Core app tables:

- `users`: local mirror of Supabase auth users.
- `chats`: conversation containers and rolling summary state.
- `messages`: persisted chat turns.
- `jobs`: searchable source records with FTS and vector fields.
- `resumes`: one current uploaded resume/profile per user.
- `resume_intents`: derived retrieval intents for profile-aware search.

Reusable mapping for future apps:

- Replace `jobs` with your searchable record table.
- Replace `resumes` with your uploaded profile/artifact table.
- Replace `resume_intents` with artifact-derived search/query intent rows.
- Keep `users`, `chats`, and `messages` for most agent chat products.

## Auth Flow

Frontend:

1. Signs in with Supabase Auth.
2. Stores access and refresh token locally.
3. Sends backend requests with:

```text
Authorization: Bearer <access_token>
```

Backend:

1. `get_current_user_id()` calls:

```text
{SUPABASE_URL}/auth/v1/user
```

2. It sends:

```text
apikey: SUPABASE_SERVICE_ROLE_KEY
Authorization: Bearer <access_token>
```

3. It returns the Supabase auth user UUID.
4. DB operations use that UUID as `user_id`.

Security rule:

- User ownership must be enforced in backend DB queries, even when Supabase service role is used.

## Storage Setup

Current path pattern:

```text
users/{user_id}/resume.pdf
users/{user_id}/resume-thumbnail.png
```

Upload pattern:

- Backend uploads bytes to Supabase Storage with service role headers.
- Backend passes `x-upsert: true` for replacing the current user artifact.
- Backend stores bucket and path in Postgres.
- Backend creates signed URLs for frontend preview.

Reusable storage path pattern:

```text
users/{user_id}/{artifact_type}/{artifact_id}/original.ext
users/{user_id}/{artifact_type}/{artifact_id}/preview.png
```

Use deterministic paths for one-current-artifact flows and UUID paths for historical/multiple artifacts.

## Async SQLAlchemy Practices

Current pattern:

```python
write_engine = create_async_engine(
    settings.DIRECT_URL,
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},
)

read_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},
)
```

Session pattern:

- `get_write_session()` commits on success.
- `get_write_session()` rolls back on error.
- `get_read_session()` only yields the session.
- DB ops use `async with`.

Why `statement_cache_size = 0`:

- Supabase poolers/PgBouncer can break asyncpg prepared statement caching in transaction pooling mode.
- Disabling the statement cache avoids prepared-statement errors.

## Async/Await Practices In This Repo

Follow these:

- FastAPI routes are async.
- DB ops await SQLAlchemy calls.
- HTTP calls use `httpx.AsyncClient`.
- OpenAI SDK calls use async clients or LangChain async methods.
- Independent retrieval branches run with `asyncio.gather`.
- Optional post-turn summarization runs with `asyncio.create_task`.

Avoid:

- Calling blocking SDKs in routes.
- Instantiating clients per request when a factory can cache them.
- Using async DB URLs in Alembic.
- Giving the frontend backend-only credentials.

## Supabase Checklist For A New Project

```text
[ ] Create Supabase project.
[ ] Enable vector extension.
[ ] Create storage bucket(s).
[ ] Configure backend SUPABASE_URL.
[ ] Configure backend SUPABASE_SERVICE_ROLE_KEY.
[ ] Configure backend DATABASE_URL with async driver.
[ ] Configure backend DIRECT_URL with async driver.
[ ] Configure backend ALEMBIC_URL with sync driver.
[ ] Configure frontend VITE_SUPABASE_URL.
[ ] Configure frontend VITE_SUPABASE_ANON_KEY.
[ ] Run Alembic migrations.
[ ] Verify auth token validation route.
[ ] Verify storage upload and signed URL generation.
[ ] Verify user_id filters on all user-owned records.
```
