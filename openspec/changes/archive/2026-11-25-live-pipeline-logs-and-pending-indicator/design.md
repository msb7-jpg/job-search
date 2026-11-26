# Design

## Context
`BackgroundRunManager` (`app/api/run_manager.py`) runs `run_pipeline` / `rejudge_pending_jobs` in a background thread, while `app/core/logging.py` writes logs to stdout/file. The SSE endpoint `/api/runs/{run_id}/stream` currently only receives high-level status messages.

## Approach
1. Attach a thread-scoped or run-scoped `logging.Handler` inside `BackgroundRunManager` during run execution that forwards formatted log records into the active run's log buffer and SSE event queue, detaching cleanly in a `finally` block.
2. Ensure `runs.py` SSE generator flushes buffered lines and streams incremental lines as they arrive, with heartbeat keepalives.
3. In `web/src/features/scraper/`, read `pending_llm_count` from `runQueries.overview()` and render a dedicated status banner/card in `ScraperControlPage` alongside the live log console.

## Verification
- Backend: Unit test `BackgroundRunManager` log capture + SSE streaming.
- Gate: `make check` exits `0`.
