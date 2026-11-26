# Tasks

- [x] 1.1 Add a scoped `logging.Handler` in `app/api/run_manager.py` to capture real-time `app.core.logging` records into the active run's buffer and SSE queue.
- [x] 1.2 Verify `/api/runs/{run_id}/stream` and `/api/runs/{run_id}/logs` emit incremental pipeline log lines.
- [x] 2.1 Add a `PENDING` LLM job count indicator and Rejudge action banner in `web/src/features/scraper/`.
- [x] 2.2 Ensure live log console auto-scrolls and renders incoming SSE log lines cleanly.
- [x] 3.1 Add/update tests for log streaming and run `make check`.
