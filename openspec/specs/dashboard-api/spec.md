# Dashboard API Specification

## Purpose
Local-first FastAPI backend serving the Command Center UI and background pipeline runs (`app/api/`).

## Requirements

### Requirement: Thin Routers and Repository Delegation
Routers in `app/api/routers/` (`jobs`, `runs`, `config`, `profile`, `tailor`) MUST inject `Annotated[Session, Depends(get_db_session)]`, delegate all queries to `app/db.py` repository functions, and return Pydantic schemas (`app/api/schemas.py`).

#### Scenario: Health and SPA serving
- **WHEN** `GET /api/health` is requested
- **THEN** the API returns `{"status": "ok"}`, and when `web/dist/index.html` exists, non-API paths serve the SPA

### Requirement: Background Run Execution and SSE Streaming
`POST /api/runs/trigger` and `POST /api/runs/rejudge` MUST execute via `BackgroundRunManager` (`app/api/run_manager.py`) and stream real-time backend pipeline log lines (provider progress, counts, Layer 1/2 decisions, and errors) via `GET /api/runs/{run_id}/stream` and `GET /api/runs/{run_id}/logs`.

#### Scenario: Triggering a scrape or rejudge run
- **WHEN** a run is triggered via `/api/runs/trigger` or `/api/runs/rejudge`
- **THEN** it runs asynchronously in a background thread and updates `ScrapeRunRow` in SQLite

#### Scenario: Real-time log streaming during scrape
- **WHEN** a scrape or rejudge run is active and `app/pipeline.py` or a provider emits log records
- **THEN** each formatted log line is pushed to the run's SSE subscriber queue and persisted in `ScrapeRunRow` without waiting for run completion
