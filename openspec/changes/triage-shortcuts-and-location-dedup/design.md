# Design

## Approach
1. Install shadcn `tooltip` via `bunx --cwd web shadcn@latest add tooltip` if not already present, and wrap triage action buttons in `web/src/features/triage/components/` with `Tooltip` showing the shortcut key.
2. Add a deterministic location normalization/deduplication helper (splitting on `,` / `;` / `\n` as appropriate without breaking `City, State, Country` tuples, or deduplicating repeated location lines).
3. In `app/db.py` (`list_jobs` / `get_job_detail`), attach sibling providers sharing `canonical_key` to `JobSummarySchema` / `JobDetailSchema`, run `make gen-api-types`, and render provider badges in the triage UI.

## Verification
- Unit tests for location deduplication and `canonical_key` sibling provider aggregation.
- `make check` exits `0`.
