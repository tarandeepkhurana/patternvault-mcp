# PatternVault MCP

PatternVault MCP is a FastMCP server that exposes reusable engineering patterns as MCP resources and tools.

The server is designed as a cross-project engineering memory layer for coding agents. It takes curated Markdown documentation from `patternvault-readmes/` and makes it available through MCP so future projects can reuse preferred architecture, folder structure, coding conventions, backend patterns, UI patterns, testing style, and implementation cards.

## What It Provides

PatternVault currently exposes:

- Markdown pattern documents as MCP resources.
- Discovery tools for listing available pattern docs.
- Read tools for fetching a specific pattern document.
- Search tools for finding relevant docs by keyword.
- Recommendation tools for mapping an engineering task to relevant docs and pattern cards.
- Pattern-card tools for extracting reusable cards from `10-pattern-cards.md`.
- Context-pack tooling for building compact, task-focused guidance bundles.

## Resources

Every Markdown file in `patternvault-readmes/` is registered as an MCP resource.

Example resource URIs:

```text
patternvault://readmes/index
patternvault://readmes/00-overview
patternvault://readmes/01-folder-structure
patternvault://readmes/06-backend-patterns
patternvault://readmes/10-pattern-cards
patternvault://readmes/supabase-setup
```

The index resource returns a JSON list of all available Markdown resources.

## Tools

The server registers these MCP tools:

```text
list_pattern_docs
read_pattern_doc
search_patterns
recommend_patterns_for_task
get_pattern_cards
build_context_pack
```

These tools make the Markdown vault easier for agents to navigate. Instead of manually reading every resource, an agent can search the vault, retrieve a specific document, find matching pattern cards, or build a compact context pack for a task.

## Project Structure

```text
src/patternvault_mcp/
  __init__.py
  auth.py
  pattern_docs.py
  resources.py
  server.py
  settings.py
  tools.py

patternvault-readmes/
pyproject.toml
uv.lock
```

Important modules:

- `server.py` creates the FastMCP server and ASGI app.
- `resources.py` registers Markdown files as MCP resources.
- `tools.py` registers MCP tools.
- `pattern_docs.py` contains reusable parsing, search, and context-pack helpers.
- `settings.py` contains environment-based configuration.
- `auth.py` contains optional app-level auth setup for self-hosted deployments.

## Configuration

Settings are read from environment variables with the `PATTERNVAULT_` prefix.

Common settings:

```text
PATTERNVAULT_SERVER_NAME=PatternVault MCP
PATTERNVAULT_SERVER_VERSION=0.1.0
PATTERNVAULT_READMES_DIR=patternvault-readmes
PATTERNVAULT_MCP_PATH=/mcp
PATTERNVAULT_STATELESS_HTTP=true
```

Optional app-level static token auth:

```text
PATTERNVAULT_AUTH_MODE=static
PATTERNVAULT_STATIC_TOKEN=<strong-token>
```

By default, `PATTERNVAULT_AUTH_MODE` is `none`.

## Local Server

Install dependencies with uv:

```powershell
uv sync
```

Inspect the server:

```powershell
uv run fastmcp inspect src/patternvault_mcp/server.py:mcp
```

Open the local FastMCP Inspector:

```powershell
uv run fastmcp dev inspector src/patternvault_mcp/server.py:mcp
```

Run the server:

```powershell
uv run fastmcp run src/patternvault_mcp/server.py:mcp --transport http --port 8000 --path /mcp
```

Run the tool smoke test:

```powershell
uv run python -m patternvault_mcp.tools
```

## Deployment

The FastMCP entrypoint is:

```text
src/patternvault_mcp/server.py:mcp
```

The ASGI app is also available as:

```text
src/patternvault_mcp/server.py:app
```

## Development Checks

Run linting:

```powershell
uv run ruff check .
```

Run tests:

```powershell
uv run pytest
```
