# Design

## Approach
1. Extend `ApplicationRow` (or add recruiter fields: `recruiter_linkedin_url`, `recruiter_connected`, `outreach_dm_md`) in `app/db.py`.
2. Add API endpoints to save recruiter info and generate an outreach DM via the existing OpenAI-compatible client.
3. Add a compact Recruiter Outreach panel in the job detail / tracker drawer with 1-click copy.

## Verification
- Unit tests for DB persistence and DM generation endpoint.
- `make check` exits `0`.
