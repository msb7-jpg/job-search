# Design

## Approach
1. **Empty MasterProfile & Toast Contrast:** Ensure `POST /api/jobs/{job_id}/tailor` raises `HTTPException(status_code=400, ...)` and frontend `onError` handlers set `variant: 'error'`. Upgrade `ToastBanner.tsx` styling for strong contrast and legibility.
2. **Resume Parser (`app/tailor/parser.py`):** Inspect LLM request/response handling, JSON extraction, and error propagation in `parse_resume_with_llm()` and `/api/profile/parse` so failures surface clearly and valid resumes parse reliably.
3. **JD Formatting:** Audit `app/shared/html_formatter.py` and provider fetchers (`linkedin`, `gupy`, `inhire`, `ciandt`, `fullstack`) to ensure HTML-to-Markdown conversion preserves newlines, headers, and bullet points, and `FormattedDescription.tsx` renders them cleanly.

## Verification
- Unit tests for `parse_resume_with_llm()`, HTML-to-Markdown formatting, and `400` response on empty `MasterProfile`.
- `make check` exits `0`.
