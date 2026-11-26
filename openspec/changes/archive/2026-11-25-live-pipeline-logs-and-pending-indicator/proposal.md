# Proposal

## Why
Currently, the Scraper UI's SSE log stream only emits coarse lifecycle messages (e.g., started fetch, started rejudge) rather than real-time backend pipeline logs, and there is no in-view indicator on the Scraper page showing how many scraped jobs remain in `PENDING` LLM evaluation when no LLM server is active.

## What Changes
- Stream real-time backend `logger` output from `app/pipeline.py` and `app/providers/` into the `BackgroundRunManager` SSE stream (`/api/runs/{run_id}/stream`) and `ScrapeRunRow.error_log`.
- Add a clear `PENDING` LLM evaluation count indicator and call-to-action in the Scraper Control view so users immediately see unjudged jobs when scraping with `--no-llm` or an offline LLM.

## Capabilities

### Modified Capabilities
- `dashboard-api`: Stream real-time Python logger records during background scrape/rejudge runs over SSE.
- `dashboard-ui`: Display real-time pipeline log lines in the Scraper live console and surface a `PENDING` LLM evaluation indicator in `ScraperControlPage`.

## Impact
- Backend: `app/api/run_manager.py`, `app/api/routers/runs.py`, `app/core/logging.py`.
- Frontend: `web/src/features/scraper/` components and hooks.
