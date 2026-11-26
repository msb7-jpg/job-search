# Delta Specification: Dashboard API

## MODIFIED Requirements

### Requirement: Thin Routers and Repository Delegation
Routers in `app/api/routers/` (`jobs`, `runs`, `config`, `profile`, `tailor`) MUST inject `Annotated[Session, Depends(get_db_session)]`, delegate all queries to `app/db.py` repository functions, and return Pydantic schemas (`app/api/schemas.py`). `GET /api/jobs` and `GET /api/jobs/{job_id}` MUST expose deduplicated location values and surface all matching providers sharing the same `canonical_key`.

#### Scenario: Health and SPA serving
- **WHEN** `GET /api/health` is requested
- **THEN** the API returns `{"status": "ok"}`, and when `web/dist/index.html` exists, non-API paths serve the SPA

#### Scenario: Cross-provider job listing
- **WHEN** two providers (e.g., `linkedin` and `gupy`) have rows with the same `canonical_key`
- **THEN** the job response includes the related provider badges/links so the user sees every source for that role
