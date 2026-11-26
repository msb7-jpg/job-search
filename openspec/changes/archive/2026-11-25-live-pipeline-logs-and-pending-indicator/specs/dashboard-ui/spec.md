# Delta Specification: Dashboard UI

## ADDED Requirements

### Requirement: Pending LLM Indicator in Scraper Control
`ScraperControlPage` MUST display the count of jobs currently in `PENDING` LLM status and allow triggering `rejudge` directly when `pending_llm_count > 0`.

#### Scenario: Scrape finishes while LLM is offline
- **WHEN** jobs remain in `PENDING` status after a scrape run
- **THEN** the Scraper Control view displays a visible pending-evaluation indicator with the exact `pending_llm_count` and an actionable Rejudge trigger
