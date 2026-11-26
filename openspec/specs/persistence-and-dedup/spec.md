# Persistence and Deduplication Specification

## Purpose
SQLite WAL persistence layer and two-key cross-run deduplication (`app/db.py`, `app/models/`).

## Requirements

### Requirement: SQLite WAL Single Source of Truth
All state MUST be persisted in `app/data/job_search.db` in WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`) via SQLAlchemy 2.0 `Mapped[]` models (`JobRow`, `JobEvaluationRow`, `ApplicationRow`, `TailoredResumeRow`, `ScrapeRunRow`).

#### Scenario: Database initialization
- **WHEN** `init_db(db_path)` runs
- **THEN** all 5 tables are created via `Base.metadata.create_all(engine)` with WAL mode and foreign keys enabled

### Requirement: Two-Key Deduplication
Jobs MUST be deduplicated across runs by `url_hash` (`UNIQUE`, 16-char `sha256` of normalized URL) and grouped across providers by `canonical_key` (indexed, non-unique 16-char `sha256` of `company|title|work_model`).

#### Scenario: Re-scraping an existing URL
- **WHEN** `upsert_scraped_jobs()` encounters an existing `url_hash`
- **THEN** it updates `last_seen_at` without duplicating the row or re-running LLM evaluation on already-evaluated jobs

#### Scenario: Cross-provider duplicate role
- **WHEN** two different providers return the same role (`canonical_key` match, distinct `url_hash`)
- **THEN** both rows are preserved so direct ATS links are not lost
