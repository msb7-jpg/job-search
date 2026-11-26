# Delta Specification: Job Scraping

## MODIFIED Requirements

### Requirement: Strategy and Registry Provider Architecture
All job providers (`linkedin`, `gupy`, `inhire`, `ciandt`, `fullstack`) MUST implement `JobProviderStrategy`, register via `ProviderRegistry`, and preserve structural formatting (line breaks, headings, bullet lists) when converting scraped HTML/JSON into `description_md`.

#### Scenario: Concurrent provider execution
- **WHEN** `run_pipeline()` executes with active providers
- **THEN** active providers are executed concurrently via `ThreadPoolExecutor` and produce `JobItem` records with deterministic `sha256`-derived IDs

#### Scenario: Scraping a job description with HTML structure
- **WHEN** a provider enriches a job posting containing `<p>`, `<br>`, `<ul>/<li>`, or heading tags
- **THEN** `description_md` preserves Markdown/paragraph and list structure instead of collapsing whitespace into a single unformatted block
