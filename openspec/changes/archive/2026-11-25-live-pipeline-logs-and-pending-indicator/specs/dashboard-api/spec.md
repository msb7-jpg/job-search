# Delta Specification: Dashboard API

## MODIFIED Requirements

### Requirement: Background Run Execution and SSE Streaming
`POST /api/runs/trigger` and `POST /api/runs/rejudge` MUST execute via `BackgroundRunManager` (`app/api/run_manager.py`) and stream real-time backend pipeline log lines (provider progress, counts, Layer 1/2 decisions, and errors) via `GET /api/runs/{run_id}/stream` and `GET /api/runs/{run_id}/logs`.

#### Scenario: Triggering a scrape or rejudge run
- **WHEN** a run is triggered via `/api/runs/trigger` or `/api/runs/rejudge`
- **THEN** it runs asynchronously in a background thread and updates `ScrapeRunRow` in SQLite

#### Scenario: Real-time log streaming during scrape
- **WHEN** a scrape or rejudge run is active and `app/pipeline.py` or a provider emits log records
- **THEN** each formatted log line is pushed to the run's SSE subscriber queue and persisted in `ScrapeRunRow` without waiting for run completion
