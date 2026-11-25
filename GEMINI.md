# `job-search` Agent Contract

Don't make assumptions or flatter. Correct me when I'm wrong; ask clarifying questions if a request doesn't make sense.
Act like a rigorous senior engineer: build practical systems that work in production, avoid bloated abstractions, and obey mechanical gates.

## Commands
- **Full Gate (Definition of Done):** `make check` (runs `ruff format --check`, `ruff check`, `check_python_hygiene.py`, `pyright`, `lint-imports`, `pytest`, `tsc`, `eslint`, `fallow`).
- **Sync API Types:** `make gen-api-types` (regenerates `web/src/api/openapi.d.ts` from FastAPI).
- **Dev Servers:** `make api` (FastAPI `:8000`) | `make web` (Vite `:5173`) | `make serve` (single-process `:8000`).
- **CLI Pipeline:** `make run` | `make rejudge` | `make export-pdf`.

## Hard Bans
- No new dependencies without explicit user approval.
- No silent `except Exception: pass` or fake fallback approvals (LLM failures must fail-closed as `PENDING`).
- No `hash()` for persistent IDs; use deterministic `hashlib.sha256`.
- No `# type: ignore`, `# noqa`, `as any`, single-letter variables (except `_` in Python), god files (>120 lines for page orchestrators, >200 for UI modules, >300 for Python), or weakened assertions to bypass `make check`.
- No editing unrelated files or refactoring outside the task scope.
- Full ownership: never keep backwards-compatibility shims, deprecated aliases, or legacy fallbacks for old code/interfaces—update callers directly and delete dead code.
- No hardcoded personal resume data, queries, or company blacklists in code—use `UserSearchConfig` (`app/data/search_config.json`) and `MasterProfile` (`app/data/master_profile.json`).

## Architecture & Spec Discipline
- Follow [`docs/PATTERNS.md`](docs/PATTERNS.md) (including its Documentation Naming Standard) and scoped rules in `app/api/AGENTS.md` and `web/AGENTS.md`.
- If you add/remove a module, DB table, API router, or CLI command, update `docs/ARCHITECTURE.md` in the same diff.
- For features larger than a bugfix, write a spec in `docs/plans/<feature>.md` before editing code.

## Definition of Done
A task is **incomplete** until `make check` exits `0` with no new warnings or suppressed checks.
