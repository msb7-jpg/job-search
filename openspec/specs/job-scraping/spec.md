# Job Scraping Specification

## Purpose
Concurrent multi-provider job scraping pipeline (`app/providers/`, `app/pipeline.py`, `app/main.py`).

## Requirements

### Requirement: Strategy and Registry Provider Architecture
All job providers (`linkedin`, `gupy`, `inhire`, `ciandt`, `fullstack`) MUST implement `JobProviderStrategy`, register via `ProviderRegistry`, and preserve structural formatting (line breaks, headings, bullet lists) when converting scraped HTML/JSON into `description_md`.

#### Scenario: Concurrent provider execution
- **WHEN** `run_pipeline()` executes with active providers
- **THEN** active providers are executed concurrently via `ThreadPoolExecutor` and produce `JobItem` records with deterministic `sha256`-derived IDs

#### Scenario: Scraping a job description with HTML structure
- **WHEN** a provider enriches a job posting containing `<p>`, `<br>`, `<ul>/<li>`, or heading tags
- **THEN** `description_md` preserves Markdown/paragraph and list structure instead of collapsing whitespace into a single unformatted block

### Requirement: CLI Entrypoints
`app/main.py` MUST expose `run` (with `--providers`, `--no-proxy`, `--no-llm`, `--no-pdf`), `rejudge`, and `export-pdf` subcommands.

#### Scenario: Rejudge without scraping
- **WHEN** `python -m app.main rejudge` is invoked
- **THEN** `rejudge_pending_jobs()` queries `PENDING` rows from SQLite and evaluates them without running scrapers
