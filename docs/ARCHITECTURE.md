The initial PRD is over-engineered for a single-user local tool. You already have the hardest part working: a zero-auth, multi-source scraper with a reactive proxy rotator, a 3-layer filter, and an LLM judge.

Rebuilding that into a "three-plane distributed architecture with Ports-and-Adapters" will burn weeks on boilerplate before you ship a single screen. Instead, evolve `job-search` into a **local-first monolith**: **SQLite + FastAPI + React (Vite)** running directly on top of your existing Python pipeline.

---

## 1. Architectural Reality Check: What to Cut vs. What to Keep

Before writing code, here is what gets cut from the initial PRD and why:

| Initial PRD Idea | Verdict | Real-World Reason |
| --- | --- | --- |
| **3 Isolated Planes + Message Queues (Celery/Redis)** | **Cut** | For 1 user scraping a few hundred jobs/day, a single FastAPI process with `ThreadPoolExecutor` / `BackgroundTasks` and SQLite (WAL mode) handles everything with zero infra overhead. |
| **Strict `typing.Protocol` Ports-and-Adapters** | **Cut** | Premature abstraction. Keep clean modules (`repositories/`, `services/`), not 15 interface files for a database you won't swap. |
| **Embedding Similarity Funnel (Layer 1.5)** | **Cut** | Your existing Layer 1 regex heuristics + `ScoringRule` already runs in <1ms and costs $0. Adding an embedding model just adds latency and maintenance for marginal gain when your local OpenAI-compatible LLM already judges the survivors. |
| **Typst for PDF Rendering** | **Cut (for now)** | You already have **Headless Chromium HTML-to-PDF** working in `pdf_exporter.py`. HTML/CSS gives you pixel-perfect ATS-friendly resumes using skills you already have, without learning a new typesetting language. |
| **Full "Autopilot" Headless Apply** | **Defer / Re-scope** | Workday, Gupy, and LinkedIn change DOMs constantly and aggressively fingerprint headless bots. Maintenance cost is massive. When you get to Phase 4, build a **Chrome Extension Co-Pilot** (Clip + Autofill) inside your real browser—it gives 80% of the speed with 5% of the breakage. |

---

## 2. Target Architecture (Local-First Monolith)

Everything lives in the existing `job-search` repository. Your CLI (`make run`) works directly on top of **SQLite as the Single Source of Truth** instead of overwritten JSON files (Telegram notifiers were removed).

* **Storage:** SQLite (`app/data/job_search.db`) in WAL mode, managed via **SQLAlchemy 2.0** (`Base.metadata.create_all`, no Alembic).
* **Backend API (Phase 2):** **FastAPI** serving both the REST API for the dashboard and triggering `app/pipeline.py` in a background thread.
* **Frontend:** **React + TypeScript + Vite + Tailwind + shadcn/ui** (served as static files by FastAPI in production, or via Vite dev server locally).
* **AI Engine:** Reuse your existing OpenAI-compatible HTTP client (`LLM_BASE_URL`) for both **Judging** (existing) and **Tailoring** (new).

---

## 3. Phase 1: Fix the Foundation (Persistence & Pipeline Upgrades)

Before building the dashboard, fix the four real bottlenecks in your current `job-search` codebase:

### 3.1 Cross-Run Persistent Deduplication (SQLite)

Right now, `vagas_linkedin.json` is overwritten daily, and fallback IDs use Python's randomized `hash(link)`.

* **Deterministic Keys:** Replace `hash(link)` with `url_hash = sha256(normalized_url)[:16]` (`UNIQUE` on `jobs`).
* **Cross-Source Dedup Key:** Add `canonical_key = sha256(f"{norm(company)}|{norm(title)}|{norm(work_model)}")[:16]` (indexed, **non-unique**). If the same role appears on LinkedIn and Gupy, group them without losing direct ATS links.
* **Upsert Logic:** When a scrape runs, if `url_hash` already exists in SQLite, only update `last_seen_at`. Never re-run the LLM Judge on a job you already evaluated yesterday.

### 3.2 Core Database Schema

Keep it tight—5 tables cover the entire MVP (Dashboard + Tailoring):

1. **`jobs`**: `id`, `url_hash` (unique), `canonical_key` (indexed), `external_id`, `provider`, `title`, `company`, `location`, `work_model`, `seniority`, `url`, `description_md`, `posted_at`, `first_seen_at`, `last_seen_at`.
2. **`job_evaluations`**: `job_id` (FK), `layer1_score`, `matched_skills_json`, `missing_skills_json`, `llm_approved` (bool), `llm_score`, `llm_reasoning`, `discard_layer`, `discard_reason`.
3. **`applications`** (User workflow state): `job_id` (FK, unique), `status` (`NEW`, `SAVED`, `TAILORING`, `READY_TO_APPLY`, `APPLIED`, `INTERVIEWING`, `OFFER`, `REJECTED`, `IGNORED`), `notes`, `applied_at`, `updated_at`.
4. **`tailored_resumes`**: `id`, `job_id` (FK), `base_profile_version`, `diff_json` (structured LLM changes), `cover_letter_md`, `qa_answers_json`, `pdf_path`, `verification_warnings_json`, `created_at`.
5. **`scrape_runs`**: `id`, `started_at`, `finished_at`, `status`, `providers_json`, `total_fetched`, `total_approved`, `total_rejected`, `error_log`.

### 3.3 Quick Pipeline Wins

* **Concurrent LLM Judging:** Wrap `avaliar_vaga_com_llm()` in a `ThreadPoolExecutor(max_workers=4)` (configurable via `Settings`, e.g., `1` for local Ollama on an 8GB GPU, `5` for cloud APIs).
* **Concurrent Providers:** Run `LinkedIn`, `Gupy`, `InHire`, `CI&T`, and `FullStack` concurrently in `executar_extracao()` since they hit completely different domains.
* **Fail-Closed / Retryable LLM State:** Instead of silently approving with `score_llm=70` when the LLM server is down, save the job with `llm_status = PENDING_LLM` so the dashboard can show a "Retry LLM Evaluation" button once your local server is back up.

---

## 4. Phase 2: The Command Center Dashboard

Build the dashboard around your actual daily workflow: **Triage → Tailor → Apply → Track**.

### 4.1 Core Views

1. **Triage Inbox (Default View):**
* Shows newly scraped `NEW` jobs that passed Layer 1 + Layer 2, sorted by `llm_score` desc.
* Split-pane layout: compact job list on the left (provider badge, company, title, score, work model, age); full formatted Job Description + LLM reasoning + matched/missing skills on the right.
* Keyboard shortcuts (`J`/`K` to navigate, `S` to Save/Shortlist, `T` to Tailor, `X` to Ignore, `O` to open original URL). Fast triage is what makes a dashboard beat a PDF report.


2. **Application Tracker (Kanban / Table Toggle):**
* Columns: `Saved` → `Ready to Apply` → `Applied` → `Interviewing` → `Offer / Rejected`.
* Drag-and-drop or 1-click status transitions, plus a notes field (e.g., recruiter name, salary discussed, next interview date).


3. **Rejection Audit Log:**
* Replaces your current `relatorio_vagas_rejeitadas.pdf`.
* Filterable table by `discard_layer` (`Layer 0`, `Layer 1`, `Layer 2`) and `discard_reason`.
* Includes a **"Rescue Job"** button: if the heuristic or LLM falsely rejected a great role, 1 click moves it to `SAVED`.


4. **Scraper Control Panel:**
* Displays recent `scrape_runs` history, active proxy pool health, and a **"Run Scrape Now"** button (with checkboxes to run specific providers, e.g., only Gupy + InHire).



### 4.2 FastAPI Contract (Minimal & Clean)

* `GET /api/jobs?status=NEW&provider=linkedin&min_score=70&search=...`
* `PATCH /api/jobs/{id}/status` (move across Kanban / rescue from rejected)
* `POST /api/runs/trigger` (starts `JobSearchMasterFacade.run()` in background, streams logs via SSE `/api/runs/{id}/stream`)
* `POST /api/jobs/{id}/tailor` (triggers Phase 3 tailoring)
* `GET /api/jobs/{id}/resume.pdf` (serves the generated PDF for inline preview/download)

---

## 5. Phase 3: Real-World AI Tailoring & PDF Engine

Replacing your external `resume-pt.md` with a structured system is what unlocks reliable tailoring without hallucinations.

### 5.1 Master Profile (`app/data/master_profile.json`)

Stop feeding raw Markdown to the LLM for rewriting. Maintain one canonical JSON file (versioned in Git) containing:

* **Immutable Facts:** Name, contact links, companies, exact job titles, exact dates, education, certifications.
* **Experience Pool:** Each role has a list of `bullets` with stable IDs (`exp_motorola_1`, `exp_motorola_2`, etc.) and tags (`python`, `django`, `vue`, `aws`, `gcp`, `ai`). You can keep *more* bullets here than fit on 1 page—the tailor selects the best ones per job.
* **Project Pool:** Your key projects with stack tags and impact metrics.
* **Q&A Fact Vault:** Simple key-value store for common screening questions (expected salary in BRL/USD, notice period, English level, location, GitHub/LinkedIn URLs).

### 5.2 Constrained Diff-Based Tailoring

When you click **"Tailor Resume"** on a job in the dashboard:

1. **Language Detection:** Automatically detect if the JD is in Portuguese or English and instruct the LLM to output in that language.
2. **Structured Output (`TailoredDiff` via Pydantic):** The LLM **never** writes the full resume. It only returns:
* `tailored_summary`: 2–3 lines aligned with the JD.
* `selected_skill_groups`: Reordered skills prioritizing JD keywords you actually have.
* `bullet_overrides`: `dict[bullet_id, rephrased_text]` — selects the top N bullets and subtly adjusts phrasing to mirror JD terminology.
* `cover_letter` (optional, toggleable).
* `missing_keywords_honest_note`: Skills the JD wants that you *don't* have (shown to you in the UI, never faked on the resume).


3. **Deterministic Anti-Hallucination Check:**
* Because the template pulls company names, titles, dates, and education directly from `master_profile.json` (not from LLM output), **structural hallucinations are impossible**.
* A lightweight post-check flags if a rephrased bullet introduced a new number/percentage not present in the original bullet, highlighting it in yellow in the UI for your review.



### 5.3 Side-by-Side Review Studio + Chromium PDF

* **UI:** Left side shows the Job Description with matched/missing keywords highlighted. Right side shows editable fields for the tailored summary and bullets, plus a live PDF preview iframe.
* **PDF Rendering:** Use a clean **Jinja2 HTML/CSS template** (single-column, ATS-safe, print-media CSS) rendered via your **existing Headless Chromium** call in `pdf_exporter.py`.
* **1-Page Guardrail:** After rendering, check page count with `pypdf` (`len(reader.pages)`). If `> 1`, surface a warning badge in the Review Studio ("Overflow: 2 pages — trim 1 bullet") rather than silently shipping a broken 2-page resume.

---

## 6. Roadmap (Deferred Until Dashboard + Tailoring Are Daily-Driven)

Once Phases 1–3 are running smoothly and saving you hours every week:

* **Phase 4 — Chrome Extension "Clipper" (High ROI, Low Maintenance):**
* **Clip to Dashboard:** When you find a job manually on LinkedIn, Wellfound, or a company site, click the extension to `POST /api/jobs/clip` directly into SQLite (bypassing scrapers and auth walls).
* **1-Click Copy / Autofill Sidebar:** When you open an ATS page for a job in your DB, the extension pulls your `Q&A Vault` + tailored summary and lets you fill fields or copy answers with 1 click inside your real, logged-in browser.


* **Phase 5 — Semi-Automated Playwright Runner (Optional):**
* Only worth building for high-volume, predictable ATS portals (e.g., Greenhouse, Lever, Ashby) using a persistent local browser profile in **Co-Pilot Mode** (fills fields, pauses before "Submit"). Skip full autopilot for Workday and Gupy—the ROI isn't there for a single user.



---

## 7. Concrete Repository Evolution

Your existing `job-search/` structure already separates concerns well. You only need to add `db/`, `api/`, `tailor/`, and `web/`:

```text
job-search/
├── proxy_pool/               # Standalone, package-ready reactive proxy rotator (zero app.* imports)
├── app/
│   ├── db.py                 # SQLite engine (WAL) + SQLAlchemy 2.0 models & repositories
│   ├── pipeline.py           # Concurrent scrape -> SQLite upsert -> Layer 1/2 -> PDF
│   ├── main.py               # CLI (run, rejudge, export-pdf)
│   ├── api/                  # Phase 2 (Implemented): FastAPI app, SSE run_manager, routers (jobs, runs, config, profile, tailor)
│   ├── tailor/               # Phase 3 (Implemented): LLM resume parser, MasterProfile, TailoredDiff, verifier, Jinja2/Chromium PDF
│   ├── core/                 # Settings, logging, and dynamic UserSearchConfig (search_config.json)
│   ├── providers/            # 5 providers (deterministic sha256 IDs)
│   ├── matchers/             # Layer 1 & Layer 2 (concurrent + fail-closed LLM)
│   └── exporters/            # Shared Chromium render_html_to_pdf() + legacy executive PDFs
└── web/                      # Phase 2–3 (Implemented): React 19 + Vite + TanStack Query/Table + Preact Signals + dnd-kit + Geist
```

### Recommended Build Order

1. **Week 1:** Add SQLite schema + deterministic `canonical_key` + wire `JobSearchMasterFacade` to upsert into SQLite (keeping `make run` working).
2. **Week 2:** Build FastAPI endpoints + React Triage Inbox & Kanban Tracker. Start using it daily instead of reading PDFs.
3. **Week 3:** Convert your `Miguel's Resume - Backend.md` / `Full-stack.md` into `master_profile.json`, build the `TailoredDiff` LLM service, and add the Review Studio + Chromium 1-page PDF generator.