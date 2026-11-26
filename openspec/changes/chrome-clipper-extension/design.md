# Design

## Approach
1. Backend (`POST /api/jobs/clip`): Accept `{ url, raw_text }`, run a structured LLM extraction prompt to populate `JobItem` fields, compute `url_hash` + `canonical_key`, upsert into `jobs`, and optionally run Layer 1 + Layer 2 evaluation.
2. Chrome Extension (Manifest V3): Simple popup with URL (pre-filled from active tab) and pasted job description textarea, posting to `http://127.0.0.1:8000/api/jobs/clip`. Autofill is explicitly out of scope for this change.

## Verification
- Backend unit tests for `POST /api/jobs/clip` parsing and SQLite upsert.
- `make check` exits `0`.
