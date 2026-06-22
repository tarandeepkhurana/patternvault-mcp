# Data Modeling

The reusable data modeling pattern is Postgres-first: normalized core tables, JSONB for flexible extracted metadata, arrays for small tag lists, pgvector for semantic search, and TSVECTOR for lexical search.

## Model Location

All ORM models live in:

```text
src/db/models.py
```

All migrations live in:

```text
src/db/migrations/versions/
```

Alembic is configured by:

```text
alembic.ini
src/db/migrations/env.py
```

## Base Conventions

Reusable conventions:

- `id`: UUID primary key with `uuid.uuid4`.
- `created_at`: timezone timestamp with DB default `func.now()`.
- `updated_at`: timezone timestamp with `onupdate=func.now()`.
- `user_id`: UUID foreign key for user-owned records.
- `JSONB`: raw source payloads, parsed model output, flexible metadata.
- `ARRAY(Text)`: small lists used for filtering or display.
- `Vector(1536)`: OpenAI embedding vectors.
- `TSVECTOR`: Postgres full-text search column.
- Explicit indexes for frequently filtered fields.

## Current Tables And Reusable Shape

### `users`

Purpose:

- Local mirror of Supabase auth users.
- Stores auth metadata useful to the app.

Reusable pattern:

- Use the Supabase auth user id as the local primary key.
- Create the row lazily when the user creates a chat or uploads an artifact.
- Do not store passwords.

### `chats`

Purpose:

- Durable conversation container per user.
- Stores title, rolling summary, and cached retrieval state.

Reusable fields:

- `conversation_summary`
- `summary_message_count`
- `retrieved_jobs` as JSONB, adaptable to `retrieved_artifacts`
- `last_retrieval_query`
- `last_retrieval_filters`
- `retrieval_updated_at`

Pattern:

- Store compact cache for follow-up questions.
- Store summary counters so old messages can be summarized incrementally.

### `messages`

Purpose:

- Durable user/assistant message history.

Reusable fields:

- `chat_id`
- `message_type`: `user`, `assistant`, or `system`
- `content`
- optional structured result cache as JSONB

Pattern:

- Persist completed turns after the agent finishes.
- Load only messages after the summary cutoff for current context.

### `jobs`

Product-specific concept:

- Job/internship listing.

Reusable table pattern:

- External source identifiers: `source`, `source_job_id`, `source_url`.
- Display fields: title, description, organization, location-like fields.
- Filter fields: type, mode, tags, numeric ranges.
- Search fields: `embedding_text`, `embedding`, `search_vector`.
- Source data: `raw_payload`, `extra_metadata`.
- Lifecycle: `status`, `is_active`, `scraped_at`, `last_updated_at`.
- Deduplication: `dedupe_key` unique.

Adaptation examples:

- For invoices: source invoice id, vendor, amount, due date, categories, embedding text.
- For contracts: source id, parties, clauses, effective date, jurisdiction, embedding text.
- For support tickets: source id, customer, status, tags, priority, embedding text.

### `resumes`

Product-specific concept:

- User resume profile.

Reusable artifact/profile pattern:

- One current artifact per user via unique `user_id`.
- Raw extracted text.
- Parsed structured JSON.
- Whole-artifact embedding.
- Original file metadata.
- Supabase Storage bucket and path.

Adaptation examples:

- Current policy document per user.
- Current company profile per tenant.
- Uploaded dataset description per project.

### `resume_intents`

Product-specific concept:

- Search intents derived from a resume.

Reusable pattern:

- Store multiple query intents derived from one artifact/profile.
- Preserve position/order.
- Store human-readable label, query text, evidence, and embedding.
- Replace the child collection when the source artifact changes.

Use this when an uploaded artifact should produce several retrieval branches.

## Relationships

Current relationships:

- `User` has many `Chat`.
- `Chat` has many `Message`.
- `User` has one current `Resume` through unique user id.
- `Resume` has many `ResumeIntent`.

Cascade rules:

- User deletion cascades chats/messages/resumes.
- Resume deletion cascades intents.

Future rule:

- Use cascade for records that cannot stand alone without their parent.
- Do not cascade shared source records unless they are tenant-owned.

## Indexing Patterns

Examples from `jobs`:

- Scalar filter indexes: source, job_type, work_mode, remote, posted_at, is_active.
- GIN indexes on arrays: skills, categories, eligibility, cities.
- pgvector index: `ivfflat` with cosine ops.
- FTS index: GIN on `search_vector`.

Reusable rule:

- Add indexes for high-cardinality lookup and common filters.
- Add GIN indexes for array overlap filters.
- Add vector indexes only after data volume justifies approximate nearest neighbor search.
- Keep active/lifecycle filters indexed when most queries hide inactive records.

## Migration Style

Pattern:

- Alembic uses `settings.ALEMBIC_URL`.
- Migrations are kept under `src/db/migrations/versions`.
- Postgres-specific constructs may need hand-written migration code.
- Supabase SQL editor can be used for triggers/functions that are awkward during early prototyping, but production projects should migrate them explicitly.

Important:

- App DB URLs use async drivers.
- Alembic URLs use sync SQLAlchemy drivers.

## DTO/API Payload Mapping

DB ops convert rows to dictionaries:

```python
return [dict(row) for row in rows]
```

Rules:

- Convert UUIDs to strings before returning API payloads.
- Convert timestamps to ISO strings when they leave the DB layer.
- Keep embeddings out of API payloads unless a server-side service needs them.
- Return compact records for lists and full records for details.

Pattern from jobs:

- `list_jobs()` returns lightweight cards.
- `get_jobs_by_ids()` returns full details.

Apply this to any domain: list endpoints should be small; detail endpoints can include long text and child arrays.

## Product-Specific Fields

Do not copy these blindly:

- `stipend_min`, `duration_days`, `eligibility`, `work_functions`.
- India-specific defaults such as `country = "India"` and `salary_currency = "INR"`.
- Job categories and Internshala source metadata.

Copy the pattern behind them:

- Normalize external source fields into stable internal columns.
- Keep original source payload/metadata for debugging.
- Store both machine-friendly fields and display-friendly labels.

