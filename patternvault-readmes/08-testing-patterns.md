# Testing Patterns

This repo currently has no formal pytest suite. It has one diagnostic script:

```text
scripts/test_embedding_endpoint.py
```

For future projects, keep the diagnostic script idea but add real tests. The patterns below describe how this architecture should be tested.

## Recommended Test Structure

```text
tests/
  unit/
    agent/
    services/
    db/
    utils/
  integration/
    routes/
    db/
    streaming/
  e2e/
    test_chat_flow.py
  fixtures/
```

Keep tests outside `src/`.

## Unit Tests

Unit test pure logic and boundary helpers without real providers.

Good unit targets:

- `src/agent/tool_calling.py`: streamed tool-call merge and JSON arg parsing.
- `src/services/retrieval/hybrid_merge.py`: reciprocal rank fusion.
- `src/services/retrieval/query_parser.py`: fallback behavior with mocked LLM.
- `src/services/resume/resume_parser.py`: normalization helpers.
- `src/services/resume/resume_embedding.py`: embedding text builder.
- `src/services/resume/resume_profile.py`: profile and intent context builders.
- `src/services/streaming/chat_stream_service.py`: `sse_event()` formatting.
- `src/utils/scraper_utils.py`: parse/normalize helpers.

Unit test style:

- Prefer deterministic inputs and expected dictionaries/lists.
- Mock LLM calls at the factory boundary.
- Mock embedding generation instead of calling OpenAI.
- Validate edge cases: empty inputs, invalid JSON, duplicate values, invalid UUIDs.

## Integration Tests

Integration tests should exercise real boundaries with controlled dependencies.

Route integration:

- Authenticated `/chat/sessions`.
- `/chat/stream` event order with mocked agent stream.
- `/pdf/upload` validation for file type and size.
- `/pdf/current` when no artifact exists and when one exists.
- `/voice/transcribe` validation for audio content type.
- `/jobs` query param filtering.
- `/jobs/{job_id}` 404 behavior.

DB integration:

- `get_write_session()` commits and rolls back.
- `create_chat_session()` creates missing user row.
- `load_chat_state()` filters by `chat_id` and `user_id`.
- `upsert_resume()` replaces one resume per user.
- `replace_resume_intents()` deletes old child rows and inserts new ones.
- `upsert_jobs()` deduplicates by `dedupe_key`.

Use a real Postgres test database for pgvector/TSVECTOR behavior. SQLite will not cover the important Postgres-specific parts.

## Streaming Tests

Test SSE as a protocol, not just final text.

Expected sequence examples:

```text
status -> token* -> done
status -> jobs -> token* -> done
error
```

Assertions:

- Each SSE block has `event:` and `data:`.
- `data` is valid JSON.
- `done` contains `final_answer`.
- `error` stops the stream.
- Tool result events do not get mixed into assistant Markdown.

## Mocking Style

Mock at stable boundaries:

- `LLMFactory.get_*_llm()`.
- `EmbeddingFactory.get_openai_embedding_client()`.
- `generate_embedding()` and `generate_embeddings()`.
- `httpx.AsyncClient` calls to Supabase Auth/Storage.
- `run_agent_stream()` when testing `chat_stream_service`.
- `retrieve_jobs()` when testing tools.

Avoid mocking internal helper functions if the public service boundary can be mocked instead.

## Fixture Style

Useful fixtures:

- `user_id`: fixed UUID.
- `chat_id`: fixed UUID.
- `auth_headers`: `Authorization: Bearer test-token`.
- `fake_resume`: parsed data plus embedding.
- `fake_jobs`: compact records with ids, titles, source URLs, scores.
- `mock_llm_response`: structured Pydantic-compatible output.
- `async_session`: test DB session wrapped in transaction rollback.

For uploaded files:

- Use in-memory `BytesIO`.
- Include filename and content type.
- Test both valid and invalid content.

## LLM Tests

Do not use real LLM calls in unit tests.

Test:

- Prompt payload construction.
- Structured output parsing with fake model responses.
- Fallback paths when model call raises.
- Normalization after model output.
- Candidate limits before reranking.

Keep a small number of manual diagnostic scripts for provider credentials. They should print compact success/failure reports and never dump secrets.

## Retrieval Tests

Unit:

- `_build_filters()`.
- `_merge_branch_filters()`.
- `_normalize_retrieval_mode()`.
- `_select_overlapping_resume_intent()`.
- RRF ordering and dedupe behavior.

Integration:

- Insert records with text, arrays, and embeddings.
- Verify FTS returns lexical matches.
- Verify vector search filters active records.
- Verify retrieval continues when one branch fails.

## Auth Tests

Test cases:

- Missing bearer token returns 401.
- Wrong scheme returns 401.
- Supabase Auth API failure returns 503.
- Non-200 Supabase Auth response returns 401.
- Response missing user id returns 401.
- Valid response returns UUID.

Mock `httpx.AsyncClient.get`.

## Background Task Tests

For summarization:

- Test threshold logic.
- Test odd/even cutoff behavior.
- Test no-op when not enough new messages exist.
- Test fallback keeps existing summary when LLM fails.

Do not require background tasks to finish in route tests unless the route explicitly depends on their result.

## What Not To Test As Universal Behavior

Product-specific examples:

- Exact job category names.
- Internshala HTML selectors.
- Exact JobLens prompt wording.
- Current frontend layout labels.

Reusable behavior:

- Source adapter returns normalized records.
- Ingestion dedupes before upsert.
- Prompt construction includes compact context.
- Streaming contract stays stable.

