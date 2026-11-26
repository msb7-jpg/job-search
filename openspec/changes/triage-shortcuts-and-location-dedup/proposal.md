# Proposal

## Why
Triage action buttons (`Tailor`, `Save`, `Ignore`, `Blacklist`, `Open`) currently display inline keyboard shortcut text, cluttering the UI. Additionally, comma-separated `Other locations` strings show duplicate entries, and cross-provider duplicate jobs (`canonical_key`) should clearly surface all matching providers for the same role.

## What Changes
- Move keyboard shortcut hints on triage action buttons into hover tooltips (using shadcn `Tooltip`) for a cleaner button bar.
- Split and deduplicate comma-separated `Other locations` values before display.
- Surface all matching providers on a job when `canonical_key` matches across multiple providers.

## Capabilities

### Modified Capabilities
- `dashboard-ui`: Clean triage action buttons with tooltip shortcuts and deduplicated location display.
- `dashboard-api`: Include cross-provider `canonical_key` siblings/providers in job list/detail responses.

## Impact
- Backend: `app/db.py`, `app/api/schemas.py`, `app/api/routers/jobs.py`.
- Frontend: `web/src/features/triage/`, shadcn `Tooltip` component (`web/src/components/ui/`).
