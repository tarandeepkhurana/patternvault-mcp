# Pattern Cards

## Pattern: Thin FastAPI Router

Purpose:
Keep HTTP handling separate from business logic.

When to use:
Every API resource or workflow endpoint.

When not to use:
Tiny throwaway scripts without HTTP.

Files/folders involved:
`src/routes/*.py`, `src/main.py`.

Implementation shape:
Define `APIRouter`, request models, dependencies, and delegate to services or DB ops.

Example from this repo:
`src/routes/chat.py` defines `ChatRequest` and returns `StreamingResponse` from `stream_chat_response()`.

Adaptation notes:
Rename route files around new resources, such as `documents.py` or `projects.py`.

Common mistakes:
Putting SQL, prompt construction, or multi-step workflows inside route handlers.

## Pattern: Typed Settings Object

Purpose:
Centralize env/config names and defaults.

When to use:
Any service with provider keys, DB URLs, model names, or feature limits.

When not to use:
Single-file scripts with no deployable runtime.

Files/folders involved:
`src/config.py`.

Implementation shape:
Use `BaseSettings`; required secrets are typed fields, non-secret values can have defaults.

Example from this repo:
`Settings` defines OpenAI, database, Supabase, and message-history config.

Adaptation notes:
Group fields by provider and add `.env.example` in future projects.

Common mistakes:
Calling `os.getenv()` throughout the codebase or exposing backend secrets to frontend.

## Pattern: Central Runtime Logging

Purpose:
Keep app logs readable while suppressing noisy SDK/framework logs.

When to use:
Any service with async providers, DB calls, and agent flows.

When not to use:
Small scripts where `logging.basicConfig` is enough.

Files/folders involved:
`src/logging_config.py`, `src/main.py`.

Implementation shape:
Call `configure_runtime_logs()` once during import/startup; maintain app and noisy logger lists.

Example from this repo:
`PrettyConsoleFormatter` pretty-prints structured log args and indents multiline logs.

Adaptation notes:
Add new logger names as new services are created.

Common mistakes:
Logging raw documents, auth tokens, full prompts, or secrets.

## Pattern: Async Read/Write Session Boundary

Purpose:
Separate DB engine/session lifecycle from business logic.

When to use:
FastAPI apps using SQLAlchemy async.

When not to use:
Apps using a different persistence SDK with its own unit-of-work pattern.

Files/folders involved:
`src/db/client.py`, `src/db/*_ops.py`.

Implementation shape:
Create async engines, sessionmakers, and context managers for reads/writes.

Example from this repo:
`get_write_session()` commits after yield and rolls back on exception.

Adaptation notes:
Keep `statement_cache_size=0` when using Supabase pooler/PgBouncer with asyncpg.

Common mistakes:
Opening sessions in routes or manually committing in multiple layers.

## Pattern: DB Operation Module

Purpose:
Hide SQL/session details behind feature-specific functions.

When to use:
Every table aggregate or persistence capability.

When not to use:
One-off migration scripts.

Files/folders involved:
`src/db/chat_ops.py`, `src/db/job_ops.py`, `src/db/resume_ops.py`.

Implementation shape:
Expose functions like `create_*`, `load_*`, `upsert_*`, `replace_*`, `list_*`.

Example from this repo:
`load_chat_state(chat_id, user_id)` loads chat, messages, retrieval cache, and resume context.

Adaptation notes:
Return dictionaries or domain DTOs, not raw ORM objects.

Common mistakes:
Letting services duplicate SQL or returning user-owned rows without `user_id` filtering.

## Pattern: Cached LLM Factory

Purpose:
Centralize model configuration and reuse configured LangChain wrappers.

When to use:
Multiple services need different LLM workloads.

When not to use:
A one-off script with one model call.

Files/folders involved:
`src/factories/llm_factory.py`, `src/services/llm/warmup.py`.

Implementation shape:
Class-level cache plus lock; one create/get pair per workload.

Example from this repo:
`get_chat_llm()`, `get_query_parser_llm()`, `get_reranker_llm()`, `get_resume_parser_llm()`.

Adaptation notes:
Choose model, streaming, temperature, timeout, and reasoning settings per workload.

Common mistakes:
Creating new model wrappers per request or scattering model names across services.

## Pattern: Cached Embedding Client Factory

Purpose:
Reuse the SDK client while passing embedding model per API call.

When to use:
Embedding APIs where the model is a request parameter.

When not to use:
Libraries that expose a reusable configured embedding wrapper and you standardize on it.

Files/folders involved:
`src/factories/embedding_factory.py`, `src/utils/embeddings.py`.

Implementation shape:
Cache `AsyncOpenAI`, call `client.embeddings.create(model=..., input=...)`.

Example from this repo:
`generate_embedding()` and `generate_embeddings()` use the cached client.

Adaptation notes:
Keep embedding dimension aligned with DB `Vector(...)`.

Common mistakes:
Changing embedding model without migrating vector dimensions.

## Pattern: Startup Warmup

Purpose:
Catch configuration errors early and prepare cached runtime objects.

When to use:
Services with DB, LLM factories, or compiled agents.

When not to use:
Long indexing or scraping jobs that would block API startup.

Files/folders involved:
`src/main.py`, `src/services/llm/warmup.py`, `src/agent/runtime.py`, `src/db/client.py`.

Implementation shape:
FastAPI lifespan awaits warmup, DB ping, and agent initialization.

Example from this repo:
`warmup_models()`, `ping_database()`, `initialize_agent()`.

Adaptation notes:
Keep warmup bounded and deterministic.

Common mistakes:
Doing slow remote inference or data ingestion during web server startup.

## Pattern: Typed Agent State

Purpose:
Make runtime state explicit and safe to pass through the agent.

When to use:
Any multi-step agent or chat workflow.

When not to use:
Single stateless LLM calls.

Files/folders involved:
`src/agent/state.py`, `src/services/chat/state_builder.py`.

Implementation shape:
Use a `TypedDict` with ids, current query, messages, durable memory, cached retrieval results, and optional profile/artifact data.

Example from this repo:
`AgentState` stores `user_id`, `chat_id`, `messages`, `conversation_summary`, `retrieved_jobs`, and `resume`.

Adaptation notes:
Rename product-specific keys, such as `retrieved_jobs`, to `retrieved_artifacts`.

Common mistakes:
Passing privileged state through model-visible tool args instead of server-owned state.

## Pattern: State Builder Service

Purpose:
Build per-request agent state from durable DB data.

When to use:
Chat agents with persisted history or user profile context.

When not to use:
Stateless completion endpoints.

Files/folders involved:
`src/services/chat/state_builder.py`, `src/db/chat_ops.py`.

Implementation shape:
Load DB state, append current human message if not already present, return `AgentState` fields.

Example from this repo:
`build_initial_state()` prevents duplicate current-query messages.

Adaptation notes:
Add additional durable context here, not in route handlers.

Common mistakes:
Rebuilding state from frontend payloads instead of trusted backend persistence.

## Pattern: SSE Streaming Service

Purpose:
Convert internal agent events into frontend-consumable SSE events.

When to use:
Chat, long-running generation, retrieval, or processing workflows that need progressive UX.

When not to use:
Fast JSON operations that complete quickly.

Files/folders involved:
`src/services/streaming/chat_stream_service.py`, `src/routes/chat.py`.

Implementation shape:
Yield `event: <name>\ndata: <json>\n\n`; persist final result after stream completion.

Example from this repo:
`stream_chat_response()` emits status/token/jobs/error/done.

Adaptation notes:
Define typed structured events for your domain.

Common mistakes:
Mixing progress text into assistant output or forgetting a final `done`.

## Pattern: Streamed Tool-Call Normalizer

Purpose:
Turn provider-specific streamed tool chunks into normal tool-call dicts.

When to use:
Streaming LLM tool calls.

When not to use:
Non-streaming tool calls that already arrive complete.

Files/folders involved:
`src/agent/tool_calling.py`, `src/agent/streaming_agent.py`.

Implementation shape:
Accumulate chunks by index, merge id/name/args, parse JSON at iteration end.

Example from this repo:
`normalize_streamed_tool_calls(tool_calls_by_index)`.

Adaptation notes:
Keep this utility provider-tolerant; args may be dicts or JSON strings.

Common mistakes:
Executing a tool before its streamed args are complete.

## Pattern: Runtime Tool Executor

Purpose:
Separate model-visible tool schema from server-side execution context.

When to use:
Tools need user id, cached results, auth state, or fallback behavior.

When not to use:
Pure deterministic tools that need only model-provided args.

Files/folders involved:
`src/agent/tools/search_jobs.py`, `src/agent/streaming_agent.py`.

Implementation shape:
Define `@tool` for schema; define `execute_*_tool(args, state)` for actual runtime execution.

Example from this repo:
`execute_search_jobs_tool()` resolves resume mode from state and handles missing resume.

Adaptation notes:
Use executors to enforce permissions and resolve user-visible references to internal ids.

Common mistakes:
Letting the LLM choose `user_id`, tenant id, or privileged flags.

## Pattern: Compact Prompt Context Builder

Purpose:
Put useful state in the prompt without flooding the context window.

When to use:
Agents with profile data, cached retrievals, or conversation summaries.

When not to use:
Structured extraction where the entire input is already the task.

Files/folders involved:
`src/agent/nodes.py`, `src/agent/streaming_agent.py`.

Implementation shape:
Build short text sections with status markers, limited lists, and selected fields.

Example from this repo:
`_build_resume_context_for_prompt()` and `_build_retrieved_jobs_context_for_prompt()`.

Adaptation notes:
Use `Status: none`, `Status: available`, and bounded lists.

Common mistakes:
Dumping raw DB rows, embeddings, private files, or unlimited message history into the prompt.

## Pattern: Rolling Conversation Summary

Purpose:
Keep long-term chat memory without loading every message.

When to use:
Persistent chat systems where conversations can grow.

When not to use:
Short-lived sessions or stateless APIs.

Files/folders involved:
`src/services/llm/summarizer.py`, `src/db/chat_ops.py`, `src/db/models.py`.

Implementation shape:
Store `conversation_summary`, `summary_message_count`, fetch new messages after cutoff, summarize when threshold is reached.

Example from this repo:
`maybe_summarize_from_db()` summarizes after 8 new messages while keeping the last 8 fresh.

Adaptation notes:
Adjust thresholds by token budget and domain risk.

Common mistakes:
Summarizing too aggressively or losing user preferences/decisions.

## Pattern: Retrieval Cache For Follow-Ups

Purpose:
Let the agent answer follow-up questions about recently retrieved records.

When to use:
Search agents where users ask "compare these" or "what about the second one?"

When not to use:
Fresh-search-only systems with no follow-up context.

Files/folders involved:
`src/db/models.py`, `src/db/chat_ops.py`, `src/agent/streaming_agent.py`.

Implementation shape:
Store retrieved records, last query, filters, and update timestamp on the chat.

Example from this repo:
`update_chat_retrieved_jobs()` persists results after `search_jobs`.

Adaptation notes:
Use compact list records, and fetch full details through a detail tool.

Common mistakes:
Keeping cache only in memory or exposing internal UUIDs unnecessarily.

## Pattern: Query Parser With Structured Output

Purpose:
Turn natural language into semantic query plus filters.

When to use:
Search/retrieval systems with mixed semantic and structured constraints.

When not to use:
Simple exact-match search boxes.

Files/folders involved:
`src/services/retrieval/query_parser.py`, `src/services/llm/prompts.py`.

Implementation shape:
Pydantic schema, structured LLM output, normalization validator, fallback to raw query.

Example from this repo:
`ParsedJobQuery` extracts work mode, paid status, stipend, duration, skills, categories, and cities.

Adaptation notes:
Replace filters with your domain fields.

Common mistakes:
Treating inferred filters as hard constraints when the user did not state them.

## Pattern: Hybrid Retrieval Pipeline

Purpose:
Improve recall and precision by combining lexical search, vector search, fusion, and reranking.

When to use:
Search over rich text records where keywords and semantics both matter.

When not to use:
Small exact lookup tables.

Files/folders involved:
`src/services/retrieval/*`.

Implementation shape:
Parse query, build filters, run FTS and vector branches with `asyncio.gather`, fuse with RRF, rerank top candidates.

Example from this repo:
`retrieve_jobs()` calls `_retrieve_normal()` or `_retrieve_with_resume()`.

Adaptation notes:
Swap `jobs` for your searchable record type.

Common mistakes:
Running vector search only, ignoring explicit filters, or reranking too many candidates.

## Pattern: Branch Failure Isolation

Purpose:
Keep retrieval working if one recall branch fails.

When to use:
Multi-branch retrieval with optional external dependencies.

When not to use:
Critical single-source transactions where partial results are invalid.

Files/folders involved:
`src/services/retrieval/retrieval_pipeline.py`.

Implementation shape:
Wrap each branch in `_safe_search(stage_name, awaitable)` and return `[]` on failure.

Example from this repo:
FTS can fail while vector search still returns candidates, or vice versa.

Adaptation notes:
Log exceptions and surface reduced confidence if needed.

Common mistakes:
Letting one optional retrieval branch fail the whole chat turn.

## Pattern: Reciprocal Rank Fusion

Purpose:
Merge multiple ranked lists without requiring comparable raw scores.

When to use:
Combining FTS, vector, profile-intent, or source-specific retrieval lists.

When not to use:
When all scores are calibrated and directly comparable.

Files/folders involved:
`src/services/retrieval/hybrid_merge.py`.

Implementation shape:
For each ranked list, add `1 / (k + rank + 1)` by document id; sort by fused score.

Example from this repo:
`reciprocal_rank_fusion_many()` merges arbitrary ranked lists.

Adaptation notes:
Keep original docs by id and add an `rrf_score`.

Common mistakes:
Concatenating lists without dedupe or trusting incomparable scores.

## Pattern: LLM Reranker

Purpose:
Use a bounded structured LLM call as final precision layer.

When to use:
Candidates require nuanced fit scoring.

When not to use:
High-volume low-latency search where LLM cost is unacceptable.

Files/folders involved:
`src/services/retrieval/reranker.py`, `src/services/llm/prompts.py`.

Implementation shape:
Convert candidates to compact text, call structured LLM, attach scores/reasons, sort.

Example from this repo:
`RERANK_CANDIDATE_LIMIT = 20` bounds reranker input.

Adaptation notes:
Keep descriptions truncated and include only decision-relevant fields.

Common mistakes:
Sending hundreds of candidates or accepting unvalidated free-text scores.

## Pattern: Profile/Artifact Intent Embeddings

Purpose:
Turn an uploaded profile/artifact into multiple retrieval branches.

When to use:
Uploaded context has several possible search angles.

When not to use:
The artifact is only used for answer generation, not retrieval.

Files/folders involved:
`src/services/resume/resume_parser.py`, `src/services/resume/resume_embedding.py`, `src/db/resume_ops.py`.

Implementation shape:
Parse artifact, derive up to N search intents, embed each intent, store as child rows.

Example from this repo:
`target_role_intents` become rows in `resume_intents`.

Adaptation notes:
Rename intents around your domain: risks, topics, obligations, entities, themes.

Common mistakes:
Letting profile branches override explicit user filters.

## Pattern: Artifact Upload Pipeline

Purpose:
Convert uploaded files into parsed, embedded, durable application context.

When to use:
Agents need user-provided documents or media.

When not to use:
Simple temporary attachments that are never parsed or reused.

Files/folders involved:
`src/services/resume/*`, `src/routes/pdf_upload.py`, `src/db/resume_ops.py`.

Implementation shape:
Validate type/size, read bytes, extract content, parse, embed, upload object, persist metadata, return preview.

Example from this repo:
`process_resume_upload()` orchestrates PDF resume processing.

Adaptation notes:
Replace PDF parser and structured schema for your artifact type.

Common mistakes:
Trusting frontend file validation or storing files without metadata.

## Pattern: Supabase Storage Signed URL

Purpose:
Let frontend preview private objects without exposing storage credentials.

When to use:
Private user-uploaded files.

When not to use:
Public static assets.

Files/folders involved:
`src/services/resume/resume_storage.py`.

Implementation shape:
Upload with service role; create short-lived signed URL; return URL to frontend.

Example from this repo:
`create_resume_signed_url()` signs PDF and thumbnail paths.

Adaptation notes:
Adjust expiration time by sensitivity and UX.

Common mistakes:
Returning service role key or raw private storage credentials.

## Pattern: Supabase Auth Dependency

Purpose:
Verify frontend Supabase sessions server-side.

When to use:
Backend APIs called by Supabase-authenticated browser clients.

When not to use:
Server-to-server APIs with a different auth scheme.

Files/folders involved:
`src/auth/dependencies.py`, `src/routes/*.py`.

Implementation shape:
Extract bearer token, call Supabase Auth `/auth/v1/user`, return UUID.

Example from this repo:
`get_current_user_id()` raises 401 or 503 depending on failure mode.

Adaptation notes:
For high-throughput systems, consider local JWT verification with `SUPABASE_JWT_SECRET`.

Common mistakes:
Accepting `user_id` from the request body or giving service role key to frontend.

## Pattern: Source Adapter Ingestion

Purpose:
Normalize external/source records into one internal schema.

When to use:
Scraping, API ingestion, ETL, partner feeds.

When not to use:
User-created records with no external source.

Files/folders involved:
`src/scraper/*`, `src/utils/scraper_utils.py`, `src/db/job_ops.py`.

Implementation shape:
Fetch source data, parse fields, update a base template, generate dedupe key, create embedding text, upsert.

Example from this repo:
Internshala modules normalize listings into the `Job` schema.

Adaptation notes:
Keep each source adapter isolated; all adapters should output the same internal dict schema.

Common mistakes:
Letting source-specific field names leak into core services.

## Pattern: Dedupe Key Upsert

Purpose:
Make ingestion idempotent.

When to use:
Repeated imports from external sources.

When not to use:
Append-only audit logs.

Files/folders involved:
`src/utils/scraper_utils.py`, `src/db/job_ops.py`.

Implementation shape:
Create stable dedupe key from source identifiers; use Postgres `on_conflict_do_update`.

Example from this repo:
`upsert_jobs()` dedupes in memory by `dedupe_key` before DB upsert.

Adaptation notes:
Choose dedupe inputs that remain stable across source updates.

Common mistakes:
Using title alone as a dedupe key or allowing duplicate records before embedding.

## Pattern: Diagnostic Provider Script

Purpose:
Verify credentials/provider setup outside the web server.

When to use:
External APIs that often fail due to env or model mismatch.

When not to use:
As a replacement for automated tests.

Files/folders involved:
`scripts/test_embedding_endpoint.py`.

Implementation shape:
Load settings, call provider once, print compact success/failure and dimensions.

Example from this repo:
The script tests the configured OpenAI embedding endpoint.

Adaptation notes:
Add scripts for storage/auth only if manual operator checks are useful.

Common mistakes:
Printing secrets or relying on diagnostics for CI coverage.

## Pattern: Product-Specific Prompt Module

Purpose:
Keep prompts centralized and separate from orchestration logic.

When to use:
Any LLM-heavy app with multiple prompts.

When not to use:
Single prompt experiments.

Files/folders involved:
`src/services/llm/prompts.py`.

Implementation shape:
Define constants for system prompts and user prompt templates; services import them.

Example from this repo:
Agent, summarizer, resume parser, query parser, and reranker prompts live together.

Adaptation notes:
Copy the sectioned prompt style, not the JobLens content.

Common mistakes:
Embedding long prompts inside route or service functions.

