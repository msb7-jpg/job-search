# Proposal

## Why
Jobs found manually on LinkedIn posts, Wellfound, or gated company sites cannot always be scraped automatically. A lightweight Chrome Extension that lets the user paste a job description (and optional post/job URL) and sends it to the local FastAPI daemon allows the backend to parse it into the exact same SQLite schema as scraped jobs (deferring complex ATS autofill to a later phase).

## What Changes
- Add a `POST /api/jobs/clip` endpoint on the local FastAPI server that accepts raw pasted job text + URL, uses the LLM to extract structured fields (`title`, `company`, `location`, `work_model`, `description_md`), and upserts the job into SQLite with `url_hash` and `canonical_key`.
- Build a minimal Chrome Extension (Manifest V3) communicating with the local daemon (`http://127.0.0.1:8000`) to clip/paste job descriptions and links directly into `job-search`.

## Capabilities

### New Capabilities
- `chrome-clipper`: Chrome Extension client communicating with the local FastAPI daemon to clip/paste manual job postings.

### Modified Capabilities
- `dashboard-api`: Add `POST /api/jobs/clip` endpoint with LLM parsing and SQLite upsert.

## Impact
- Backend: `app/api/routers/jobs.py`, `app/api/schemas.py`, `app/db.py`, LLM job-clipper parser helper.
- Extension: New `extension/` directory (Manifest V3 popup + background/API client).
- Docs: Update `docs/ARCHITECTURE.md` when implemented.
