# PatternVault Overview

These docs extract reusable engineering patterns from this repository for future Python microservices, especially agentic AI systems that combine FastAPI, async database access, Supabase/Postgres, LLM calls, embeddings, streaming chat, uploads, and retrieval.

This is not a product spec for JobLens. JobLens is the product-specific example. The reusable value is the structure: thin HTTP routes, service modules, async DB operations, cached model factories, typed agent state, streaming event contracts, tool execution wrappers, retrieval pipelines, upload pipelines, and Supabase operational boundaries.

## Best Fit For Future Projects

Use these patterns when building:

- Python FastAPI microservices for AI agents.
- Chat systems that stream tokens/status/tool results over SSE.
- RAG or search systems using full-text search plus vector search.
- Apps that parse uploaded artifacts, create embeddings, store files, and persist metadata.
- Supabase-backed products with Auth, Postgres, Storage, pgvector, and Alembic migrations.
- Small product backends where the frontend owns UX but backend owns auth verification, persistence, retrieval, and agent orchestration.

These patterns are less useful for:

- Pure batch scripts with no API boundary.
- Large distributed systems that already require separate services, message brokers, and deployment units.
- Frontend-only prototypes.
- Projects where the database is not the source of truth.

## High-Value Reusable Patterns

- `src/main.py`: FastAPI application assembly with startup warmup in a lifespan context.
- `src/config.py`: one typed settings object loaded from `.env`.
- `src/logging_config.py`: centralized runtime logging and noisy-library suppression.
- `src/routes/*`: thin route modules that validate inputs and delegate work.
- `src/services/*`: domain orchestration services grouped by capability.
- `src/db/client.py`: async SQLAlchemy engine/session factories with read/write boundaries.
- `src/db/*_ops.py`: database operation modules that hide SQL/session details from routes.
- `src/db/models.py`: SQLAlchemy model definitions with indexes, JSONB, arrays, vector fields, and relationships.
- `src/factories/*_factory.py`: cached OpenAI/LangChain clients and model wrappers.
- `src/agent/state.py`: typed agent runtime state.
- `src/agent/streaming_agent.py`: streaming tool loop that emits normalized runtime events.
- `src/agent/tools/*`: tool declarations plus runtime executors that inject hidden state.
- `src/services/retrieval/*`: parse, lexical search, vector search, fusion, reranking.
- `src/services/resume/*`: reusable artifact pipeline shape: validate, read, parse, embed, store, persist.

## Product-Specific Examples

Treat these as examples to adapt, not universal patterns:

- Jobs, internships, resumes, companies, stipends, cities, and Internshala sources.
- `Job`, `Resume`, `ResumeIntent`, and job-specific prompts.
- The exact `JOBLENS_AGENT_SYSTEM_PROMPT` wording.
- Scraper category modules under `src/scraper/intershala`.
- Frontend labels such as "Use resume", "Jobs and internships", and category names.

## How Another Agent Should Use These Docs

1. Start with `01-folder-structure.md` to understand where new code belongs.
2. Read `02-architecture-patterns.md` before creating service boundaries.
3. Use `03-coding-conventions.md` while writing Python.
4. Use `04-feature-pattern.md` as the feature implementation checklist.
5. Read `supabase-setup.md` before touching database/auth/storage configuration.
6. Use `10-pattern-cards.md` as a menu of reusable patterns to apply selectively.

When building a new project, copy the shape, not the domain. For example, copy "artifact upload pipeline" from the resume flow, but rename the domain concepts to match the new product: document, contract, invoice, portfolio, dataset, audio sample, or whatever the service actually handles.

## Core Dependency Direction

Keep the dependency direction one-way:

```text
routes
  -> services / agent entrypoints
      -> db ops / factories / utilities / external clients
          -> config
```

Routes should not contain SQL. DB modules should not import FastAPI routes. Factories should not know product workflows. Agent tools should call services, not duplicate business logic.

