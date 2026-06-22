# Agent Usage Guide

This file is written for a coding agent applying these patterns to a new repository.

## Your Goal

Use this repo as a pattern source for a Python agentic AI microservice. Copy architectural shapes and implementation idioms. Do not copy product-specific job/resume concepts unless the new product actually needs them.

## Read Order

1. `00-overview.md`
2. `01-folder-structure.md`
3. `02-architecture-patterns.md`
4. `03-coding-conventions.md`
5. `supabase-setup.md` if Supabase is involved
6. `04-feature-pattern.md` when adding a feature
7. `10-pattern-cards.md` for reusable implementation cards

## What To Copy

Copy these shapes:

- `src/main.py` style app assembly and lifespan warmup.
- `src/config.py` typed settings object.
- `src/logging_config.py` central logging idea.
- `src/routes/*` thin route modules.
- `src/services/<capability>/` workflow modules.
- `src/db/client.py` async engine/session boundary.
- `src/db/*_ops.py` operation modules returning DTO dictionaries.
- `src/factories/*_factory.py` cached clients/models.
- `src/agent/state.py` typed state.
- `src/agent/streaming_agent.py` style streaming tool loop.
- `src/agent/tool_calling.py` streamed tool-call normalization.
- Retrieval pipeline shape: parse, FTS, vector, fusion, rerank.
- Artifact upload shape: validate, read, parse, embed, store, persist.

## What To Adapt

Adapt these before copying:

- Table names and fields.
- Prompt constants.
- Tool names and tool policies.
- Retrieval filters.
- Artifact parser schema.
- Storage bucket and paths.
- SSE structured result event names.
- Frontend labels and UX.
- Scraper/source adapter modules.

Example adaptation:

```text
JobLens resume upload
  -> contract upload
  -> extract clauses
  -> parse parties/dates/risks
  -> embed full contract
  -> store contract intents
  -> retrieve related clauses or obligations
```

## What To Avoid Copying Blindly

Do not blindly copy:

- Internshala scraping modules.
- Job category lists.
- India-specific salary/currency/location defaults.
- The exact JobLens system prompt.
- Hardcoded model choices without checking project cost/latency needs.
- `docker-compose.yml`, which appears stale relative to the current FastAPI/Supabase structure.
- Local uploaded PDF files.
- Real `.env` values.

## Questions To Ask Before Applying A Pattern

Ask these and then implement with reasonable defaults:

- What is the durable user-owned artifact or record?
- Does the agent need chat memory?
- Should the feature stream, or can it return normal JSON?
- Which values are public frontend env and which are backend-only secrets?
- Is profile/artifact context a hard filter or a recall expansion?
- Which operations must be user_id scoped?
- Does the LLM need a tool, or can a normal service call handle it?
- Is this a prototype-only synchronous step that should become a worker later?

## Implementation Rules

When adding code:

- Put HTTP code in `routes`.
- Put orchestration in `services`.
- Put SQL/session work in `db/*_ops.py`.
- Put model/client creation in `factories`.
- Put prompts in a prompt module.
- Put pure helpers close to the feature unless shared.
- Keep route bodies short.
- Keep tool schemas safe.
- Inject privileged state from server-side `AgentState`, not tool args.
- Return compact payloads to LLM tools.
- Return full details through explicit detail endpoints/tools.

## Supabase Rules

If using Supabase:

- Frontend gets only `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE_URL`.
- Backend keeps `SUPABASE_SERVICE_ROLE_KEY`, DB URLs, and OpenAI keys.
- Backend verifies auth tokens.
- Backend filters user-owned rows by `user_id`.
- Use async SQLAlchemy URLs for runtime.
- Use sync SQLAlchemy URL for Alembic.
- Enable pgvector before vector migrations.

## Agent Streaming Rules

If building streaming chat:

- Keep a stable event protocol.
- Use status events for backend progress.
- Use token events for assistant deltas.
- Use structured events for retrieved artifacts.
- Persist final turns after completion.
- Persist retrieval cache for follow-up questions.
- Summarize older messages asynchronously when the threshold is reached.

## Retrieval Rules

If building retrieval:

- Parse user query into semantic text plus structured filters.
- Run lexical and vector recall independently.
- Fuse before reranking.
- Limit reranker candidates.
- Keep hard user filters hard.
- Add profile/artifact-derived branches carefully.
- Store embeddings at ingestion/upload time, not during every search when avoidable.

## Upload Rules

If building artifact upload:

- Enforce file type and size server-side.
- Store original object in durable storage.
- Extract/parse content.
- Normalize parsed output.
- Generate embeddings.
- Persist metadata and storage path.
- Return signed preview URLs, not service credentials.

## Final Checklist Before You Finish A New Repo

```text
[ ] Routes are thin.
[ ] Services own workflows.
[ ] DB ops own sessions and SQL.
[ ] Settings are centralized.
[ ] Secrets are backend-only.
[ ] Supabase auth is verified server-side.
[ ] User-owned queries filter by user_id.
[ ] Model clients come from factories.
[ ] Streaming events are documented.
[ ] Upload size/type validation exists.
[ ] LLM structured outputs are validated and normalized.
[ ] Tests mock providers and cover boundaries.
```

