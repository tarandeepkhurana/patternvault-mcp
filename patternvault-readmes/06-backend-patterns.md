# Backend Patterns

This repo has a real FastAPI backend. The reusable backend pattern is a thin-controller, service-oriented, async Python API with Supabase Auth, async SQLAlchemy, LLM factories, SSE streaming, and upload/storage workflows.

## Route Pattern

Routes live under `src/routes/`.

Typical route shape:

```python
router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    query: str
    chat_id: UUID
    use_resume_profile: bool = False

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    return StreamingResponse(...)
```

Rules:

- Define request models beside the route when they are small.
- Use `Query` constraints for query params.
- Inject auth via `Depends`.
- Delegate immediately to a service or DB op.
- Keep route return shapes simple and JSON-compatible.

## Service Pattern

Services live under `src/services/<capability>/`.

Good services:

- Orchestrate multiple steps.
- Know workflow ordering.
- Catch provider errors only when there is a safe fallback.
- Call DB ops instead of opening sessions directly.
- Call factories instead of instantiating model clients directly.

Examples:

- `services/streaming/chat_stream_service.py` owns SSE encoding and chat turn lifecycle.
- `services/resume/resume_upload_service.py` owns upload processing.
- `services/retrieval/retrieval_pipeline.py` owns multi-branch retrieval.
- `services/voice/transcription_service.py` owns audio validation and transcription.

## DB Access Pattern

`src/db/client.py` creates:

- `write_engine` from `settings.DIRECT_URL`.
- `read_engine` from `settings.DATABASE_URL`.
- `WriteSessionLocal`.
- `ReadSessionLocal`.
- `get_write_session()` with commit/rollback.
- `get_read_session()` without commit.

Reusable pattern:

```python
async with get_write_session() as session:
    session.add(row)
```

Do not manually commit in route functions. Let the write session context manager own transaction lifecycle.

## Validation Pattern

Validation happens in layers:

- FastAPI/Pydantic validates request shape.
- Service validates files and workflow inputs.
- Structured LLM output is validated by Pydantic models.
- DB operations normalize ids, embeddings, and upsert payloads.
- SQL query params clamp limits and normalize filters.

Examples:

- Audio must have `content_type` starting with `audio/` and must be under `MAX_AUDIO_BYTES`.
- Resume upload must be `application/pdf` and under 5 MB.
- Query params clamp job list limits to `1..100`.
- Rerank scores are constrained to `0.0..1.0`.

## Auth Boundary

`src/auth/dependencies.py` verifies Supabase bearer tokens:

```text
Authorization: Bearer <access_token>
  -> GET {SUPABASE_URL}/auth/v1/user
      -> returns Supabase auth user id
          -> backend uses UUID as user_id
```

Rules:

- Never accept `user_id` from request JSON for user-owned operations.
- Use `Depends(get_current_user_id)` on authenticated routes.
- Lazily create local `User` rows when needed.
- Filter user-owned DB reads by both resource id and `user_id`.

## Persistence Pattern

Tables are modeled with SQLAlchemy in `src/db/models.py`.

Patterns:

- UUID primary keys.
- Timezone timestamps.
- JSONB for parsed data and metadata.
- `ARRAY(Text)` for small tag lists.
- `Vector(1536)` for OpenAI embeddings.
- `TSVECTOR` for Postgres full-text search.
- Indexes for filters and lookup fields.
- Cascades from users to chats/messages/resumes.

Upserts:

- `jobs` upsert by `dedupe_key`.
- `resumes` upsert by unique `user_id`.
- `resume_intents` are replaced as a child collection.

## Streaming Backend Pattern

`stream_chat_response()` is the boundary between FastAPI and the agent runtime:

- Builds initial state.
- Iterates `run_agent_stream`.
- Encodes SSE with `sse_event()`.
- Persists final turn after model completion.
- Starts background summarization.
- Emits final `done`.

SSE headers:

```text
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

## Background Work Pattern

The repo uses lightweight background work:

```python
asyncio.create_task(maybe_summarize_from_db(...))
```

Use this only when:

- The work is optional or can finish after the response.
- Failure does not invalidate the user response.
- The task can be retried or safely skipped.

For production-heavy jobs, use a worker queue instead.

## Upload And Storage Pattern

Resume upload illustrates the pattern:

- Validate content type and size.
- Read bytes once.
- Extract/parse/embed.
- Upload durable PDF and thumbnail to Supabase Storage.
- Persist storage path and parsed metadata in Postgres.
- Return signed URLs for frontend preview.

Storage paths are deterministic by user:

```text
users/{user_id}/resume.pdf
users/{user_id}/resume-thumbnail.png
```

Adapt the path for other artifacts, such as `users/{user_id}/contracts/{artifact_id}.pdf`.

## Testing Hooks

The repo currently has a diagnostic script rather than a full suite:

- `scripts/test_embedding_endpoint.py` verifies the embedding provider and configured model.

Future backend tests should mock:

- `LLMFactory`.
- `EmbeddingFactory`.
- Supabase Auth HTTP call.
- Supabase Storage HTTP calls.
- External scrapers.

Integration tests should cover:

- Authenticated route access.
- DB upserts and ownership filters.
- SSE event order.
- Upload validation.
- Retrieval fallback behavior.

