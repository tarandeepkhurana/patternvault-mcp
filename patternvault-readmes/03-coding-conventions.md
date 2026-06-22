# Coding Conventions

These conventions describe the implementation taste of the Python backend. Use them as defaults for future agentic microservices.

## Python Style

- Use Python 3.13 style type hints: `str | None`, `list[dict]`, `dict[str, str]`.
- Prefer `async def` for route handlers, DB operations, LLM calls, HTTP calls, and file-upload flows.
- Keep modules small and capability-named.
- Keep comments short and structural. Use them to label workflow stages when the function has several steps.
- Use dictionaries for service-layer DTOs when the app is small; use Pydantic response models when API contracts need stricter enforcement.

## Naming

File naming patterns:

- Routes: `src/routes/<resource>.py`
- Services: `src/services/<capability>/<verb_or_concept>.py`
- DB operations: `src/db/<aggregate>_ops.py`
- Factories: `src/factories/<provider_or_capability>_factory.py`
- Agent tools: `src/agent/tools/<tool_domain>.py`
- Migrations: Alembic-generated revision files under `src/db/migrations/versions/`

Function naming patterns:

- Route handlers: short HTTP action names, such as `stream_chat`, `upload_resume`, `get_jobs`.
- DB reads: `get_*`, `list_*`, `load_*`.
- DB writes: `create_*`, `upsert_*`, `update_*`, `replace_*`, `remove_*`.
- Services: workflow verbs, such as `process_resume_upload`, `transcribe_audio`, `retrieve_jobs`.
- Internal helpers: leading underscore, such as `_normalize_embedding`.

## Async/Await Practices

Reusable async practices from this repo:

- Use `httpx.AsyncClient` for outbound HTTP.
- Use `AsyncOpenAI` for OpenAI SDK calls that are not LangChain wrappers.
- Use SQLAlchemy `AsyncSession` with `async_sessionmaker`.
- Use `async with` around DB sessions and HTTP clients.
- Use `await file.read()` for uploads.
- Use `asyncio.gather()` for independent retrieval branches.
- Use `asyncio.create_task()` only for non-critical post-response work, such as summarization.

Operational rules:

- Every async function should either await I/O directly or orchestrate async functions.
- Do not call long blocking work directly inside a route if it can become slow. PDF rendering and parsing are acceptable in a prototype, but future production services should offload heavy CPU work to a worker or threadpool.
- Do not create a new OpenAI client or LLM wrapper on every request if a cached factory can own it.

## Configuration

`src/config.py` uses one `Settings` class:

```python
class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DATABASE_URL: str
    DIRECT_URL: str
    ALEMBIC_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"
```

Rules:

- Put env names in `Settings`; do not call `os.getenv()` throughout the codebase.
- Give safe defaults only for non-secret values.
- Use `extra = "ignore"` so local env files can contain provider values not used by this service.
- Keep frontend env separate and prefixed with `VITE_`.

## Logging

Use named loggers:

```python
logger = logging.getLogger("retrieval.retrieval_pipeline")
```

Reusable style:

- Log workflow stage starts and completions.
- Log counts, ids, mode names, and compact previews.
- Avoid logging full secrets, auth tokens, raw private documents, or unbounded prompt payloads.
- Use `logger.exception()` inside broad exception handlers to preserve tracebacks.
- Configure noisy third-party loggers centrally.

## Error Handling

Patterns in the repo:

- Route-facing validation errors raise `HTTPException`.
- Auth failures return `401`.
- Provider connectivity failures return `503` when auth verification cannot be completed.
- Services catch external failures when a fallback is acceptable.
- Retrieval branch failures are isolated with `_safe_search()` so one branch can fail while the other continues.
- DB write sessions rollback on exception.

Future rule:

- Fail fast for invalid user input.
- Degrade gracefully for optional AI/retrieval branches.
- Preserve tracebacks in logs while returning safe user-facing messages.

## Typed LLM Outputs

For structured LLM tasks, define a Pydantic model close to the service:

- `ParsedJobQuery` in `query_parser.py`.
- `ParsedResume` and nested item models in `resume_parser.py`.
- `RerankResult` in `reranker.py`.

Pattern:

```python
structured_llm = llm.with_structured_output(MySchema)
result = await structured_llm.ainvoke(messages)
return result.model_dump()
```

Always normalize after structured output. Pydantic validates shape; domain normalization handles casing, dedupe, fallback labels, and search terms.

## SQL Style

The repo uses both SQLAlchemy ORM and textual SQL:

- ORM models define schema and relationships.
- `select()` is used for simple ORM reads.
- `text()` is used for Postgres-specific FTS/vector queries and flexible filtered reads.
- SQL params are bound separately; user input is not interpolated directly.

When using dynamic SQL:

- Build condition strings from server-owned branches only.
- Keep user values in `params`.
- Clamp limits, such as `min(max(limit, 1), 100)`.

## Factory Style

Factories are class-based caches with a lock:

- `LLMFactory` caches configured `ChatOpenAI` instances.
- `EmbeddingFactory` caches the OpenAI async client.

Rule:

- Cache model wrappers when they are configured objects.
- Cache SDK clients when API calls specify model per request.
- Keep model choice centralized by workload: chat, parser, reranker, summarizer, transcription, embedding.

## Prompt Style

Prompts live in `src/services/llm/prompts.py`.

Reusable conventions:

- One constant per prompt.
- Use XML-like sections for policy clarity.
- Include schema intent and output rules for structured tasks.
- Keep product policy separated from service code.
- Build compact runtime context separately, then format it into the prompt.

Product-specific:

- The exact JobLens role, job answer policy, and source policy should not be copied to unrelated domains.

## Implementation Idioms

Repeated idioms worth copying:

- Deduplicate while preserving order with `list(dict.fromkeys(values))`.
- Normalize optional embeddings so `[]` becomes `None` before DB writes.
- Use `uuid.UUID` parsing at DB/API boundaries.
- Store server-owned timestamps with timezone-aware `datetime.now(timezone.utc)` or DB `func.now()`.
- Return compact tool payloads to the LLM to reduce context size.
- Keep full details available through a second detail-fetch tool or endpoint.

