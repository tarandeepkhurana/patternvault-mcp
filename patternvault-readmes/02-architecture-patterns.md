# Architecture Patterns

The reusable architecture is a layered async FastAPI backend with agent orchestration, retrieval, persistence, and external provider clients separated by responsibility.

## Layering

```text
HTTP client / frontend
  -> FastAPI route
      -> service or agent stream service
          -> agent tools / retrieval / upload / LLM service
              -> db ops / factories / utilities
                  -> settings / external providers
```

Rules:

- Routes validate inputs and call services.
- Services orchestrate workflows.
- DB operation modules own sessions, SQL, and persistence DTOs.
- Factories own client/model construction.
- Agent tools call services or DB ops through runtime executors.
- Config is imported downward; it should not import app code.

## Application Startup

`src/main.py` uses a FastAPI lifespan function:

```text
configure_runtime_logs()
lifespan:
  await warmup_models()
  await ping_database()
  await initialize_agent()
```

Reusable pattern:

- Fail early when the DB or critical clients are misconfigured.
- Compile/cache long-lived agent graphs at startup.
- Warm model wrappers, not necessarily remote model inference.
- Keep startup work bounded; move slow indexing or ingestion to jobs.

## Route And Service Boundaries

Routes are intentionally thin:

- `routes/chat.py` defines request models and returns `StreamingResponse`.
- `routes/pdf_upload.py` accepts `UploadFile` and delegates to `process_resume_upload`.
- `routes/jobs.py` translates query parameters to DB filters.
- `routes/voice.py` accepts an audio file and delegates to transcription.

Reusable boundary:

```text
route = HTTP concerns
service = workflow concerns
db ops = persistence concerns
factory = provider setup concerns
```

## State Ownership

State is split by durability:

- Durable state: Postgres tables such as users, chats, messages, jobs, resumes, intents.
- Runtime state: `AgentState` passed through the agent for one request.
- Cached runtime clients: factories and compiled agent in process memory.
- Frontend state: UI filters, local chat id cache, in-progress stream rendering.
- Storage objects: PDFs and thumbnails in Supabase Storage, referenced by DB metadata.

For future projects, decide where each new piece of state belongs. Do not hide durable business state in the frontend or in an in-memory singleton.

## Agent Data Flow

Streaming chat flow:

```text
POST /chat/stream
  -> stream_chat_response()
      -> build_initial_state()
          -> load_chat_state()
      -> run_agent_stream(state)
          -> build prompt messages from state
          -> stream LLM chunks
          -> collect streamed tool calls
          -> execute tools
          -> persist retrieved artifacts/cache
          -> emit status/token/jobs/error/done events
      -> save_chat_turn()
      -> create background summarization task
```

Reusable patterns:

- Build state from DB at the edge of the request.
- Keep agent state explicit and typed.
- Let the LLM see only safe, compact context.
- Use runtime executors to inject hidden server state into tools.
- Persist important tool results before the final answer is sent.

## SSE Streaming Contract

The backend emits event names instead of a single opaque token stream:

- `status`: user-facing progress.
- `thinking`: model reasoning summary when available.
- `token`: assistant text delta.
- `jobs`: retrieved structured artifacts.
- `error`: recoverable request failure.
- `done`: final answer.

Reusable rule:

- The frontend should not infer backend stages from text tokens.
- Each event should carry JSON data with stable field names.
- Keep `done` as the only final success marker.

## Tool Boundaries

The repo separates model-visible tool declarations from runtime execution:

- Tool declarations are decorated with `@tool` and expose a safe schema.
- Runtime executors accept `args` plus `AgentState`.
- Executors can apply auth, cached context, fallback behavior, or hidden flags.

Example:

- The model can call `search_jobs(query, retrieval_mode)`.
- `execute_search_jobs_tool(args, state)` resolves `use_resume_profile`, checks whether a resume exists, and calls retrieval.

Reusable pattern:

- Never rely on the LLM to pass sensitive or authoritative values such as `user_id`, tenant id, permissions, or server-side feature flags.

## Retrieval Architecture

Retrieval follows a four-stage pattern:

```text
parse query
  -> run FTS and vector branches
      -> reciprocal rank fusion
          -> LLM rerank
```

For profile-aware search, the same pattern adds extra branches:

- User query branch.
- Stored intent branches.
- Profile embedding branch.

Reusable pattern:

- Keep hard user filters stable across all branches.
- Add profile/document context as recall expansion, not as a replacement for user intent.
- Use a final precision layer to score a bounded candidate set.

## Upload/Artifact Pipeline

Resume upload is product-specific, but the pipeline is reusable:

```text
validate file
  -> read bytes
  -> enforce size/type
  -> persist temporary/local copy if needed
  -> extract text/content
  -> structured LLM parse
  -> normalize parsed data
  -> generate embeddings
  -> upload durable object and preview artifact
  -> upsert metadata and vectors
  -> return preview URLs and parsed summary
```

Use this shape for invoices, contracts, pitch decks, transcripts, code bundles, medical forms, or any artifact-driven agent system.

## Database Boundary

`src/db/client.py` owns engines and session factories:

- `get_write_session()` commits on success and rolls back on error.
- `get_read_session()` yields a read session without committing.
- `ping_database()` verifies connectivity on startup.

DB ops return dictionaries that are safe for services/routes. They do not return raw ORM objects to the frontend.

## Dependency Direction

Allowed:

- `routes` import `services`, `db ops`, and auth dependencies.
- `services` import `db ops`, factories, prompts, utilities.
- `agent` imports services, tools, factories, state.
- `db ops` import `db.client` and `db.models`.
- `factories` import `config`.

Avoid:

- DB modules importing FastAPI route modules.
- Factories importing services.
- Routes containing raw SQL.
- Prompts embedded in route functions.
- Frontend env or UI state leaking into backend settings.

## Product-Specific Architecture

Product-specific pieces in this repo:

- Job search schema and filters.
- Resume parsing schema.
- Internshala ingestion modules.
- JobLens prompt policies.

Reusable pieces:

- Artifact parsing and embedding pipeline.
- Profile-aware retrieval modes.
- Agent state and streaming loop.
- Supabase-backed auth/storage/persistence boundary.

