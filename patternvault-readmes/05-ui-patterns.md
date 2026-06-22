# UI Patterns For Frontend Owners

This doc is intentionally light. The Python microservice should define contracts and provide backend capabilities; the frontend owner should design and implement the UX.

The reusable backend-to-frontend ideas in this repo are useful for agent streaming, audio input, and artifact upload.

## Streaming Chat Contract

The frontend should consume `/chat/stream` as an SSE-style response. The backend sends named events:

- `status`: progress text such as "Searching..." or "Processing results...".
- `thinking`: optional model reasoning summary text.
- `token`: assistant text delta.
- `jobs` or future domain result event: structured retrieved artifacts.
- `error`: safe error message.
- `done`: final answer.

Frontend guidance:

- Render assistant messages incrementally from `token`.
- Render `status` separately from assistant text.
- Treat structured events as data, not Markdown.
- Stop loading only after `done` or `error`.
- Keep a parser that handles partial stream chunks and splits on blank lines.

## Auth Contract

The frontend should:

- Use Supabase Auth with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
- Send the access token to the backend as `Authorization: Bearer <token>`.
- Refresh expired sessions client-side.
- Never receive or store the service role key, database URL, direct URL, Alembic URL, or OpenAI API key.

The backend verifies the bearer token and maps it to the Supabase user id.

## Artifact Upload

The repo uses resume upload as a product-specific example. The reusable UX pattern:

- Let the user select a file.
- Upload with `multipart/form-data`.
- Show upload/parsing progress.
- Backend returns parsed summary plus preview URLs.
- Frontend stores preview state and lets the user inspect the uploaded artifact.
- If the artifact can personalize the agent, expose a clear toggle such as "Use uploaded profile/context".

Frontend owner decisions:

- Drag-and-drop vs file picker.
- Preview layout.
- Retry/remove controls.
- Progress UI.
- File validation copy.

Backend should still enforce file type and size.

## Audio Input

The repo keeps realtime voice simple:

```text
browser records audio
  -> POST /voice/transcribe
      -> backend returns text
          -> frontend inserts text into composer
```

Frontend guidance:

- Use browser `MediaRecorder`.
- Keep states like `idle`, `listening`, and `transcribing`.
- Stop media tracks after recording.
- Send audio as `multipart/form-data`.
- Insert transcript into the text composer instead of auto-submitting unless product UX says otherwise.

The Python microservice should not own microphone UX, waveform UI, browser permissions, or audio device handling.

## Jobs/Artifacts Browser Pattern

The current frontend has a searchable side panel for structured records. Reusable idea:

- A filterable browser lets users inspect the database outside chat.
- Chat can retrieve and discuss the same records.
- Details open in a modal or side panel.
- Agent tool results and manual browsing should share response shapes where possible.

Product-specific:

- Job cards, stipends, duration, source links, and category labels.

## Frontend Env To Request

The frontend usually needs only:

```text
VITE_API_BASE_URL
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
```

Do not give frontend:

```text
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
DIRECT_URL
ALEMBIC_URL
OPENAI_API_KEY
```

