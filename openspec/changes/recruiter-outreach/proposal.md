# Proposal

## Why
When applying or networking for a role, users often find the hiring recruiter on LinkedIn and want to track whether they've connected and send a concise, role-tailored DM without rewriting it from scratch every time.

## What Changes
- Allow associating a recruiter LinkedIn profile URL/name with a job/application, plus a boolean/status tracking whether a LinkedIn connection has been made.
- Add an LLM-powered action to draft a tailored recruiter DM based on the job description and `MasterProfile`.

## Capabilities

### New Capabilities
- `recruiter-outreach`: Associate recruiter LinkedIn profiles with jobs, track connection state, and generate tailored outreach DMs.

### Modified Capabilities
- `persistence-and-dedup`: Store recruiter profile URL, connection state, and generated DM on `ApplicationRow` (or a dedicated table).
- `dashboard-api`: Endpoints to update recruiter info/connection state and generate a tailored DM.
- `dashboard-ui`: UI controls in job detail / application tracker for recruiter tracking and DM drafting.

## Impact
- Backend: `app/db.py`, `app/api/schemas.py`, `app/api/routers/jobs.py` (or `outreach.py`), LLM prompt helper.
- Frontend: `web/src/features/triage/` and/or `web/src/features/tracker/`.
