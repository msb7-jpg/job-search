# Delta Specification: CV Tailoring

## MODIFIED Requirements

### Requirement: MasterProfile and Constrained TailoredDiff
Candidate identity, experience bullets (with stable `bullet_id`s), education, academic experiences/monitorias, skills, and `qa_vault` MUST live in `app/data/master_profile.json` (`MasterProfile`). `POST /api/jobs/{job_id}/tailor` MUST return an HTTP 4xx error (not 2xx) when `MasterProfile` is empty, `parse_resume_with_llm()` MUST reliably extract academic experiences and monitorias into `MasterProfile`, and `TailoredDiff` MUST instruct the LLM to rewrite only what is needed for the target role.

#### Scenario: Anti-hallucination verification
- **WHEN** `verify_tailored_diff()` checks a `TailoredDiff`
- **THEN** it flags unknown `bullet_id`s and newly invented numeric metrics/percentages as `VerificationWarning` items

#### Scenario: Tailoring with empty MasterProfile
- **WHEN** `POST /api/jobs/{job_id}/tailor` is called while `MasterProfile` has no identity/experiences
- **THEN** the API returns HTTP `400` with a clear error detail so the UI displays an error notification

#### Scenario: Parsing resume via LLM
- **WHEN** a user uploads a PDF, Markdown, or text resume to `POST /api/profile/parse`
- **THEN** `parse_resume_with_llm()` extracts text, handles LLM response formatting/timeouts cleanly, and returns a valid `ParsedResumeResult`

#### Scenario: Parsing academic experience and monitorias
- **WHEN** a resume containing university education and academic monitorias/projects is parsed via `parse_resume_with_llm()`
- **THEN** those entries are preserved in `MasterProfile` with stable IDs so they can be selected and tailored

### Requirement: Chromium ATS PDF Rendering and Page Guardrail
`render_tailored_resume_pdf()` (`app/tailor/renderer.py`) MUST render the Jinja2 template (`resume.html.j2`) via shared `render_html_to_pdf()` and surface an overflow warning only when page count exceeds **2 pages**.

#### Scenario: Serving tailored resume PDF
- **WHEN** `GET /api/jobs/{job_id}/resume.pdf` is requested
- **THEN** the generated PDF is served inline/downloadable and page overflow warnings are surfaced if page count exceeds the configured limit

#### Scenario: 2-page resume passes guardrail
- **WHEN** a rendered tailored resume PDF is 1 or 2 pages long
- **THEN** no page-overflow `VerificationWarning` is emitted; an overflow warning is emitted only when `len(pages) > 2`
