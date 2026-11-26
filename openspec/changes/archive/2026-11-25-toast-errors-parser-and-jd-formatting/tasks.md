# Tasks

- [x] 1.1 Ensure `POST /api/jobs/{job_id}/tailor` returns HTTP 400 when `MasterProfile` is empty and frontend mutations trigger `variant: 'error'` toasts.
- [x] 1.2 Improve `web/src/components/ToastBanner.tsx` contrast, positioning, and readability.
- [x] 2.1 Debug and fix `app/tailor/parser.py` (`parse_resume_with_llm`) and `/api/profile/parse`.
- [x] 3.1 Preserve Markdown/list/paragraph structure in `app/shared/html_formatter.py` and provider fetchers, and verify rendering in `FormattedDescription.tsx`.
- [x] 4.1 Add tests for parser and JD formatting, then run `make check`.
