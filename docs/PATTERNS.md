# Rigid Engineering Patterns (`job-search`)

This document defines the mandatory architectural, backend, and frontend patterns for `job-search`. All future features and refactors MUST follow these patterns so the codebase stays fast, minimal, and consistent.

---

## 1. Backend Patterns (Python 3.14 + FastAPI + SQLite)

### 1.1 Local-First Monolith & SQLite WAL
- **Single Source of Truth:** All job, evaluation, application, tailored resume, and scrape run state lives in SQLite (`app/data/job_search.db`) in WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`) via SQLAlchemy 2.0 `Mapped[]` models in [`app/db.py`](file:///home/miguelsb/workspace/job-search/app/db.py).
- **No Premature Infra:** Do not add Celery, Redis, Alembic, or Ports-and-Adapters boilerplate. Use `ThreadPoolExecutor` and `BackgroundRunManager` (`app/api/run_manager.py`) for background execution.

### 1.2 Thin Routers + Repository Functions
- **Routers (`app/api/routers/*.py`):** Must NEVER contain raw SQLAlchemy `select(...)` queries. Call repository functions in `app/db.py` (e.g., `list_jobs`, `get_job_detail`, `update_application_status`).
- **Dependency Injection:** Always use `Annotated[Session, Depends(get_db_session)]` (satisfies Ruff `B008` and keeps FastAPI signatures clean).
- **Schemas:** Request/response contracts live in `app/api/schemas.py` (or module-local Pydantic v2 `BaseModel`s) — never return raw ORM rows.

### 1.3 Zero Hardcoding of Personal Data, Queries, or Blacklists
- **Dynamic Search Config (`app/core/user_config.py`):** Queries (`queries_jobs`, `queries_ats`, `termos_cargo_inhire`), `skills_map`, `regras_pontuacao`, filter thresholds, and `blacklisted_companies` are stored in `app/data/search_config.json` and edited via `/api/config` + `SettingsPage.tsx`.
- **Dynamic Master Profile (`app/tailor/models.py`):** Candidate identity, experience bullets (with stable IDs), education, skills, and `qa_vault` live in `app/data/master_profile.json` and are populated/edited via `/api/profile` and `/api/profile/parse` (LLM resume parser).
- **Layer 1 Blacklist Enforcement:** `avaliar_pre_filtro_job_bruto()` in `app/shared/classifiers.py` must always receive `blacklisted_companies` from `UserSearchConfig`.

### 1.4 Constrained AI Tailoring & Anti-Hallucination
- **Never generate a full resume with an LLM.** The LLM only returns `TailoredDiff` (`app/tailor/models.py`) referencing existing `bullet_id`s from `master_profile.json`.
- **Deterministic Verification:** `verify_tailored_diff()` (`app/tailor/service.py`) checks for unknown `bullet_id`s and newly invented numeric metrics/percentages.
- **1-Page ATS PDF Guardrail:** `render_tailored_resume_pdf()` (`app/tailor/renderer.py`) renders the single-column Jinja2 template via `render_html_to_pdf()` (shared Chromium helper in `app/exporters/pdf_exporter.py`) and checks `len(PdfReader(...).pages) > 1`.

### 1.5 Standalone `proxy_pool/` Boundary & Python Hygiene
- `proxy_pool/` must maintain **zero imports from `app.*`**.
- **Zero Single-Letter Variables & God-File Ban:** `scripts/check_python_hygiene.py` bans all alphabetic 1-letter identifiers (`_`-only placeholder allowed) and caps Python files at `300` lines (`app/db.py`, `app/exporters/pdf_exporter.py`, `proxy_pool/rotator.py` are legacy exceptions).
- **Complexity & Explaining Variables:** Ruff enforces `C901` (`max-complexity = 15`). Extract explaining variables for non-trivial `if` conditions and compose high-level functions so callers read like an outline.

---

## 2. Frontend Patterns (React 19 + TypeScript + Vite + Bun)

### 2.0 Mandatory `bun` & Feature-Folder Page Orchestrators
- **Package Manager & Runner:** Always use **`bun`** (`bun install --cwd web`, `bun run --cwd web ...`, `bunx --cwd web ...`). Never use `npm` or `npx`.
- **Feature-Folder + Page Orchestrator Pattern (`web/src/features/<domain>/`):** `*Page.tsx`, `ReviewStudioModal.tsx`, and `App.tsx` must be pure orchestrators (`<= 120` lines) that wire hooks/state and delegate UI to focused child components (`components/*.tsx`, `<= 200` lines).
- **Zero Single-Letter Variables & Explaining Variables:** ESLint enforces `id-length: ["error", { "min": 2 }]` and `no-restricted-syntax` against raw string literal comparisons (use `web/src/lib/constants.ts`). Use named explaining variables for complex conditionals.
- **Full TSDoc Hover Coverage:** ESLint (`eslint-plugin-jsdoc` + `eslint-plugin-tsdoc`) requires `/** ... */` docstrings on all functions, components, hooks, types, and interface properties.
- **Idiomatic Preact Signals:** Use `useSignal` and `useComputed` everywhere. `@preact/signals-react-transform` (Babel plugin in `web/vite.config.ts`) tracks `.value` reads automatically; `@preact/signals-react/runtime` (`useSignals()`) is banned. ESLint bans `useState`/`useMemo`/`useEffect`/`useRef`/`useCallback` in UI components and pages, permitting `useEffect`/`useRef` only inside `src/**/hooks/*.ts` for genuine DOM/external lifecycle subscriptions.
- **shadcn-First UI Workflow:** Before building UI primitives, dialogs, tables, selects, or overlays, search the `shadcn` MCP registry (`search_items_in_registries`, `view_items_in_registries`, `get_item_examples_from_registries`) and install via `bunx --cwd web shadcn@latest add <component>` into `web/src/components/ui/`.
- **Full Ownership (No Legacy Shims):** Never add backwards-compatibility shims or fallbacks for old interfaces—update callers directly and remove dead code.

### 2.1 TanStack Query v5 (`web/src/api/queries.ts`)
- **Query Key Factory + `queryOptions`:** Every query MUST be defined via `queryOptions(...)` paired with a hierarchical key factory (`jobKeys`, `runKeys`, `configKeys`, `profileKeys`).
- **Object-Only Mutations:** All `useMutation` calls use v5 object syntax and perform surgical `queryClient.invalidateQueries({ queryKey: ... })` in `onSuccess`.

### 2.2 TanStack Table v8 (`web/src/components/DataTable.tsx`)
- All tabular views (Rejection Audit Log, Application Table View) use the generic `<DataTable columns={...} data={...} />` wrapper with typed `ColumnDef<TData>[]`.

### 2.3 Reactive UI State & Hooks
- **Preact Signals (`@preact/signals-react`):** Cross-component UI state (active tab, selected job ID, Review Studio modal ID, SSE log buffer, toast notifications) lives in `web/src/state/signals.ts`. `@preact/signals-react-transform` automatically instruments components reading `.value`, so `useSignals()` is unnecessary and banned.
- **`@reactuses/core`:** Use `@reactuses/core` hooks (`useDebounce`, `useEventListener`, etc.) instead of hand-rolling custom debounce/hotkey effects.
- **`@dnd-kit`:** Kanban drag-and-drop uses `@dnd-kit/core` + `@dnd-kit/sortable` with `PointerSensor` (`activationConstraint: { distance: 6 }`) so card buttons remain clickable.

### 2.4 Visual Design System ("Minimalist Light-Green AI SaaS")
- **Typography:** `Geist Variable` (`--font-sans`) and `Geist Mono Variable` (`--font-mono`) for scores, IDs, dates, and logs.
- **Color Discipline:** Neutral `#FAFAFA` canvas, `#FFFFFF` cards, `1px` `#E4E4E7` (`border-zinc-200`) borders, `#09090B` primary ink. Use **very light green** (`emerald-50` / `emerald-200` / `emerald-600`) strictly for primary actions, active states, and match badges — never full-color saturated backgrounds.
- **Icons:** `lucide-react` exclusively.

---

## 3. Documentation Naming Standard

All repository documentation must follow this exact naming and directory layout:

| Location | Naming Pattern | Purpose |
| --- | --- | --- |
| `docs/<UPPER_SNAKE_CASE>.md` | `ARCHITECTURE.md`, `PATTERNS.md` | Living canonical system docs |
| `docs/plans/<kebab-case>.md` | `chrome-clipper.md` | Pre-code feature specs |
| `docs/reports/phase-<n>.md` | `phase-1.md` | Historical milestone reports |
| `AGENTS.md` / `GEMINI.md` | `GEMINI.md` (root), `AGENTS.md` (root pointer & scoped dirs) | Agent contracts & mechanical gates |
