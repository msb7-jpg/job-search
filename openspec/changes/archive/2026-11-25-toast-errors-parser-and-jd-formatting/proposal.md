# Proposal

## Why
Three usability bugs currently block daily use:
1. Triggering CV tailoring with an empty `MasterProfile` surfaces `"MasterProfile está vazio..."` in a low-contrast success-styled toast instead of an error toast, and `ToastBanner` is hard to notice.
2. "Parse Resume with LLM" (`/api/profile/parse` / `app/tailor/parser.py`) fails during normal use.
3. Job descriptions arrive and render as unformatted raw text instead of preserving structure (paragraphs, lists, headings).

## What Changes
- Fix error handling so empty `MasterProfile` (and any failed API call) triggers an `error` toast variant, and improve `ToastBanner.tsx` contrast/visibility.
- Diagnose and fix `parse_resume_with_llm()` (`app/tailor/parser.py`) and `/api/profile/parse` so uploaded PDFs/Markdown/text reliably populate `MasterProfile`.
- Preserve formatting (Markdown/HTML structure) for scraped job descriptions across providers, storage (`description_md`), and `FormattedDescription.tsx`.

## Capabilities

### Modified Capabilities
- `cv-tailoring`: Reliable LLM resume parsing (`parse_resume_with_llm`) and proper HTTP error status when `MasterProfile` is empty.
- `job-scraping`: Preserve structured formatting in scraped job descriptions (`description_md`) instead of collapsing to flat raw text.
- `dashboard-ui`: Display errors with `error` toast variant, high-contrast `ToastBanner`, and formatted job descriptions.

## Impact
- Backend: `app/api/routers/tailor.py`, `app/tailor/parser.py`, `app/providers/*/fetcher.py`, `app/shared/html_formatter.py`.
- Frontend: `web/src/components/ToastBanner.tsx`, `web/src/components/FormattedDescription.tsx`, `web/src/api/mutations.ts`.
