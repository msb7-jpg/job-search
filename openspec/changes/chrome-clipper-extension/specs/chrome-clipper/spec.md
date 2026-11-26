# Delta Specification: Chrome Clipper

## ADDED Requirements

### Requirement: Manual Job Clipping via Local Daemon
The Chrome Extension MUST communicate with the local FastAPI daemon (`POST /api/jobs/clip`) to submit a pasted job description and URL, returning the created/updated job ID and status.

#### Scenario: Clipping a pasted job description
- **WHEN** the user pastes a job description and optional post/job URL in the extension and submits
- **THEN** the daemon parses structured fields via LLM, upserts the job into SQLite using `url_hash` and `canonical_key`, and makes it visible in the Command Center Inbox
