# New Feature Pattern

Use this checklist when adding a new backend feature in the style of this repo. The example names are generic so they can be adapted to any product.

## 1. Decide The Feature Boundary

Before coding, decide:

- Is this an HTTP feature, agent tool, background ingestion flow, or all three?
- Does it need durable state?
- Does it need user auth or tenant isolation?
- Does it need streaming events?
- Does it call an LLM, embeddings API, external HTTP API, or storage provider?

Map the domain to the existing structure. For an "artifact analysis" feature:

```text
routes/artifacts.py
services/artifacts/artifact_upload_service.py
services/artifacts/artifact_reader.py
services/artifacts/artifact_parser.py
services/artifacts/artifact_embedding.py
services/artifacts/artifact_storage.py
db/artifact_ops.py
agent/tools/artifacts.py
```

## 2. Add Configuration First

If the feature needs env values:

1. Add typed fields to `src/config.py`.
2. Use safe defaults only for non-secrets.
3. Document which values are backend-only and frontend-safe.
4. Do not read env vars directly in service modules.

Example pattern:

```python
ARTIFACT_STORAGE_BUCKET: str = "artifacts"
ARTIFACT_MAX_SIZE_MB: int = 10
```

## 3. Add Data Model And Migration

If persistence is needed:

1. Add SQLAlchemy model(s) in `src/db/models.py`.
2. Add indexes for lookup fields, ownership fields, timestamps, and vector/FTS columns.
3. Generate an Alembic migration.
4. Add any Supabase SQL-editor-only objects separately if they cannot be cleanly represented in Alembic.

Reusable table conventions:

- `id` as UUID primary key.
- `user_id` as UUID foreign key for user-owned records.
- `created_at` and `updated_at` with timezone.
- `raw_payload` or `extra_metadata` as JSONB for source-specific fields.
- `embedding` as `Vector(1536)` when using OpenAI 1536-dimensional embeddings.
- `storage_bucket` and `storage_path` when objects live in Supabase Storage.

## 4. Add DB Operations

Create `src/db/<feature>_ops.py`.

Recommended shape:

- Parse/validate ids at module boundary.
- Use `get_read_session()` for reads.
- Use `get_write_session()` for writes.
- Return dictionaries, not ORM objects, to services/routes.
- Keep one function per operation: `get_*`, `list_*`, `upsert_*`, `replace_*`.
- Use `insert(...).on_conflict_do_update(...)` for idempotent ingestion or one-record-per-user resources.

Preserve boundary:

- DB ops can know schema details.
- Services should not assemble raw SQL.
- Routes should not manage sessions.

## 5. Add Service Modules

Put workflow logic in `src/services/<feature>/`.

For upload-like features, follow:

```text
validate
  -> read
  -> parse
  -> normalize
  -> embed
  -> store object
  -> persist metadata
  -> return safe response
```

For retrieval-like features, follow:

```text
parse intent
  -> run independent recall branches
  -> fuse
  -> rerank/score
  -> return compact results
```

For LLM classification/extraction:

- Define Pydantic output schema near the service.
- Use `with_structured_output`.
- Normalize result after model output.
- Add deterministic fallback when the model fails.

## 6. Add Route Module

Create or update `src/routes/<feature>.py`.

Route checklist:

- Define `router = APIRouter(prefix="/...", tags=["..."])`.
- Use Pydantic request models for JSON bodies.
- Use `UploadFile` and `File(...)` for file uploads.
- Use `Depends(get_current_user_id)` for authenticated user-owned operations.
- Convert query params to service arguments.
- Return service result directly if already safe.
- Raise `HTTPException` for HTTP-specific errors.

Register the router in `src/main.py`.

## 7. Add Agent Tool If Needed

If the feature should be model-callable:

1. Create a `@tool` declaration in `src/agent/tools/<feature>.py`.
2. Keep tool args user-facing and safe.
3. Add an executor that accepts `args` and `AgentState`.
4. Inject `user_id`, tenant id, cached artifacts, and feature flags from state.
5. Bind the tool in `streaming_agent.py`.
6. Add prompt policy that tells the model when to use the tool.

Do not expose internal ids unless the model needs them to reference cached records. Prefer resolving user-visible titles/URLs to ids in the executor.

## 8. Add Streaming Events If Needed

If the feature affects chat progress:

- Emit `status` before long work.
- Emit a typed event for structured results, such as `artifacts`, `sources`, `matches`, or `records`.
- Emit `token` only for assistant text.
- Emit `error` for recoverable failures.
- End with `done`.

Keep event names stable; frontend code will depend on them.

## 9. Update Prompt Context Builders

If the agent needs durable context:

- Add compact context builder functions.
- Include status markers such as `Status: none` or `Status: available`.
- Limit list sizes and text length.
- Avoid inserting raw sensitive documents into prompts unless required.

The repo uses this pattern for resume context and retrieved jobs context.

## 10. Add Tests Or Diagnostics

Future projects should add:

- Unit tests for pure helpers and normalization.
- Unit tests for tool arg parsing and state building.
- Integration tests for route auth, DB operations, and streaming event order.
- Mocked tests for LLM outputs and external HTTP calls.
- One diagnostic script only when manual provider verification is useful.

## Boundaries To Preserve

- Auth identity comes from backend verification, not request body.
- User-owned DB reads must filter by `user_id`.
- LLM tools cannot set privileged runtime state.
- Secrets stay in backend env only.
- Model clients come from factories.
- Long-running optional work should not block final response unless the result is required.

