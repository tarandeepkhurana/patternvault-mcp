# Folder Structure

This repo uses a compact Python service layout under `src/`, with optional frontend and scripts colocated in the repo. The reusable pattern is "one backend package with capability-based subfolders."

## Root Layout

```text
.
  README.md
  pyproject.toml
  requirements.txt
  alembic.ini
  docker-compose.yml
  docs/
  scripts/
  src/
  patternvault-readmes/
```

Root files should be project-level only:

- `pyproject.toml` / `requirements.txt`: Python runtime dependencies.
- `alembic.ini`: migration config; points to `src/db/migrations`.
- `.env`: local secrets and connection strings. Never commit real values.
- `README.md`: human setup and product overview.
- `docs/`: product or engineering notes that are useful but not runtime code.
- `scripts/`: diagnostic or operator scripts that can be run manually.
- `patternvault-readmes/`: reusable engineering pattern docs for agents.

Do not put application modules, route handlers, or DB code at the root.

## Backend Package Layout

```text
src/
  main.py
  config.py
  logging_config.py
  auth/
  routes/
  services/
  db/
  agent/
  factories/
  utils/
  scraper/
  frontend/
```

### `src/main.py`

Purpose:

- Assemble the FastAPI app.
- Configure logging.
- Register middleware.
- Run startup warmup in the lifespan handler.
- Include routers.

What belongs here:

- App metadata.
- CORS settings.
- Startup health checks such as DB ping and model/agent warmup.
- Router registration.

What should not go here:

- Route business logic.
- SQL.
- LLM prompt construction.
- Upload parsing.

### `src/config.py`

Purpose:

- Single typed settings object using `pydantic_settings.BaseSettings`.
- Env defaults for non-secret values.
- Required secrets as typed fields.

Scale pattern:

- Keep all runtime env names in one `Settings` class.
- Group variables by provider or subsystem.
- Keep frontend env separate under `src/frontend/.env`.

### `src/logging_config.py`

Purpose:

- Central logging setup.
- Named application loggers.
- Suppress noisy third-party libraries.
- Pretty-print structured log arguments.

Scale pattern:

- Add new service logger names to `APP_LOGGERS`.
- Add high-volume SDK loggers to `NOISY_LOGGERS`.

### `src/routes/`

Purpose:

- FastAPI routers grouped by HTTP surface area.
- Request/response Pydantic models.
- Dependency injection such as auth.
- Thin delegation to services or DB ops.

Examples:

- `routes/chat.py`: chat session creation and SSE streaming endpoint.
- `routes/pdf_upload.py`: artifact upload and current artifact metadata.
- `routes/jobs.py`: list and detail endpoints.
- `routes/voice.py`: audio transcription endpoint.

Reusable convention:

- Name route files after public API resources: `chat.py`, `files.py`, `voice.py`, `projects.py`.
- Use `router = APIRouter(prefix="/resource", tags=["Resource"])`.
- Keep route functions small.

### `src/services/`

Purpose:

- Business workflows and orchestration.
- Capability-based subfolders.

Current shape:

```text
services/
  chat/
  llm/
  resume/
  retrieval/
  streaming/
  voice/
```

Reusable convention:

- Put orchestration in services, not routes.
- Use subfolders when a capability has multiple files.
- Split complex workflows into narrow modules: parser, reader, embedding, storage, profile, upload service.

### `src/db/`

Purpose:

- Database engines and sessions.
- SQLAlchemy models.
- Alembic migrations.
- Operation modules per aggregate or table family.

Current shape:

```text
db/
  client.py
  models.py
  chat_ops.py
  job_ops.py
  resume_ops.py
  migrations/
```

Reusable convention:

- `client.py`: engine/session lifecycle only.
- `models.py`: table schema only.
- `*_ops.py`: database operations and DTO mapping.
- `migrations/versions/`: one migration per schema change.

Do not import FastAPI request objects into `db/`.

### `src/agent/`

Purpose:

- Agent state, graph/runtime, streaming tool loop, tool definitions, and tool-call normalization.

Current shape:

```text
agent/
  state.py
  graph.py
  runtime.py
  nodes.py
  streaming_agent.py
  tool_calling.py
  tools/
```

Reusable convention:

- `state.py`: the typed state contract.
- `runtime.py`: compile/cache the agent once.
- `graph.py`: graph wiring.
- `streaming_agent.py`: streaming loop and event emission.
- `tools/`: model-visible tools plus runtime executors.

### `src/factories/`

Purpose:

- Centralized client/model creation.
- Cache expensive or reusable clients.

Examples:

- `llm_factory.py`: caches configured `ChatOpenAI` wrappers by workload.
- `embedding_factory.py`: caches the OpenAI async client and passes embedding model per request.

### `src/utils/`

Purpose:

- Shared pure utilities or low-level helpers.

Examples:

- `embeddings.py`: provider call wrapper for single and batch embeddings.
- `scraper_utils.py`: source normalization helpers.

Avoid putting feature orchestration in `utils/`. If a helper needs DB, LLM, auth, or storage, it likely belongs in `services/`.

### `src/scraper/`

Purpose:

- Product-specific ingestion adapters and pipeline.

Reusable pattern:

- Keep source-specific scraping modules separate from normalized ingestion.
- Convert external records into the internal base schema before persistence.

Product-specific:

- Internshala category modules are specific to JobLens.

### `src/frontend/`

Purpose:

- A Vite/React frontend living beside the backend for prototype speed.

Reusable backend rule:

- Treat this folder as a client of the API, not part of backend business logic.
- Backend docs should define HTTP/SSE/auth contracts; frontend owns UI state and rendering.

## Scaling The Structure

For a new feature, add files in this order:

1. `src/db/models.py` and migration if persistent state is needed.
2. `src/db/<feature>_ops.py` for DB operations.
3. `src/services/<feature>/...` for workflow logic.
4. `src/routes/<feature>.py` for HTTP entrypoints.
5. `src/agent/tools/<feature>.py` if the agent should call it.
6. `src/services/streaming/...` only if a new event stream is needed.
7. Tests under `tests/` in a future project.

Keep names boring and capability-based. A future invoice service might use `services/invoice/invoice_upload_service.py`, `services/invoice/invoice_parser.py`, `db/invoice_ops.py`, and `routes/invoices.py`.

