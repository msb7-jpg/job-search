# Job Search Automation

Local-first monolith (**SQLite + FastAPI + React/Vite**) for scraping, deduplicating, filtering, LLM-judging, triaging, and AI-tailoring resumes for tech job listings from **LinkedIn**, **Gupy**, **InHire**, **CI&T**, and **FullStack**.

---

## Key Features

- **Zero Authentication Scraping:** Concurrent scrapers for LinkedIn, Gupy, InHire, CI&T, and FullStack backed by a standalone reactive proxy rotator (`proxy_pool/`).
- **SQLite Single Source of Truth:** WAL-mode database (`app/data/job_search.db`) with normalized `url_hash` (`UNIQUE`) cross-run deduplication and `canonical_key` cross-provider grouping.
- **Dynamic UI-Editable Config & Blacklist:** Search queries, skills, scoring rules, filter thresholds, and blacklisted companies live in `app/data/search_config.json` and are editable in the UI.
- **Fail-Closed 2-Layer Filtering:** Fast Layer 1 heuristics + concurrent OpenAI-compatible LLM Judge (`PENDING` on failure, retryable via `make rejudge` or UI).
- **Command Center Dashboard (`web/`):** Split-pane Triage Inbox (`J`/`K`/`S`/`T`/`X`/`O` shortcuts), `@dnd-kit` Kanban / TanStack Table Tracker, Rejection Audit Log with 1-click Rescue, live SSE Scraper Control, Profile Studio, and Settings.
- **AI Resume Parser & 1-Page PDF Studio (`app/tailor/`):** Upload/paste any resume to parse into `MasterProfile` + suggested queries/skills, generate constrained `TailoredDiff`s with deterministic anti-hallucination checks, and render 1-page ATS-safe PDFs via Headless Chromium + `pypdf`.

---

## Repository Structure

```text
job-search/
├── proxy_pool/                   # Standalone reactive proxy rotator (zero app.* imports)
├── app/
│   ├── api/                      # FastAPI app, schemas, SSE run manager, and routers
│   ├── core/                     # Pydantic Settings, logging, and dynamic UserSearchConfig
│   ├── db.py                     # SQLAlchemy 2.0 SQLite WAL schema (5 tables) & repositories
│   ├── models/                   # Pydantic schemas & StrEnums
│   ├── profiles/                 # Default profile schema & scoring rules
│   ├── providers/                # 5 scrapers (LinkedIn, Gupy, InHire, CI&T, FullStack)
│   ├── shared/classifiers.py     # Layer 1 heuristics & dynamic company blacklist
│   ├── matchers/                 # Keyword scoring & concurrent fail-closed LLM Judge
│   ├── tailor/                   # LLM Resume Parser, TailoredDiff, verifier, Jinja2/Chromium PDF
│   ├── exporters/pdf_exporter.py # Shared Chromium PDF helper & legacy executive PDFs
│   ├── pipeline.py               # Concurrent scrape -> SQLite upsert -> Layer 1/2 -> PDF
│   └── main.py                   # CLI entry point (run, rejudge, export-pdf)
├── web/                          # React 19 + TypeScript + Vite + TanStack + Signals + Geist UI
├── docs/
│   ├── ARCHITECTURE.md           # Local-first monolith architecture & roadmap
│   ├── PATTERNS.md               # Rigid backend, frontend & doc naming patterns
│   ├── plans/                    # Pre-code feature specs (kebab-case.md)
│   └── reports/                  # Historical phase reports (phase-<n>.md)
└── tests/                        # Pytest / unittest suite
```

---

## Usage

```bash
# Sync Python & frontend dependencies (bun is mandatory for web/)
make sync
bun install --cwd web

# Run full mechanical gate (ruff, hygiene AST, pyright, lint-imports, pytest, tsc, eslint, fallow)
make check

# Dev servers (API :8000 + Vite :5173)
make api
make web

# Single-process production serve (:8000)
make serve

# CLI pipeline
make run
make rejudge
make export-pdf
```
