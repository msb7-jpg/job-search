# CV Tailoring Specification

## Purpose
Constrained diff-based AI resume tailoring and Chromium PDF rendering (`app/tailor/`, `app/exporters/pdf_exporter.py`).

## Requirements

### Requirement: MasterProfile and Constrained TailoredDiff
Candidate identity, experience bullets (with stable `bullet_id`s), education, skills, and `qa_vault` MUST live in `app/data/master_profile.json` (`MasterProfile`). `POST /api/jobs/{job_id}/tailor` MUST return an HTTP 4xx error (not 2xx) when `MasterProfile` is empty, and `parse_resume_with_llm()` MUST reliably parse uploaded resumes into `ParsedResumeResult`.

#### Scenario: Anti-hallucination verification
- **WHEN** `verify_tailored_diff()` checks a `TailoredDiff`
- **THEN** it flags unknown `bullet_id`s and newly invented numeric metrics/percentages as `VerificationWarning` items

#### Scenario: Tailoring with empty MasterProfile
- **WHEN** `POST /api/jobs/{job_id}/tailor` is called while `MasterProfile` has no identity/experiences
- **THEN** the API returns HTTP `400` with a clear error detail so the UI displays an error notification

#### Scenario: Parsing resume via LLM
- **WHEN** a user uploads a PDF, Markdown, or text resume to `POST /api/profile/parse`
- **THEN** `parse_resume_with_llm()` extracts text, handles LLM response formatting/timeouts cleanly, and returns a valid `ParsedResumeResult`

### Requirement: Chromium ATS PDF Rendering and Page Guardrail
`render_tailored_resume_pdf()` (`app/tailor/renderer.py`) MUST render the Jinja2 template (`resume.html.j2`) via shared `render_html_to_pdf()` and check page count.

#### Scenario: Serving tailored resume PDF
- **WHEN** `GET /api/jobs/{job_id}/resume.pdf` is requested
- **THEN** the generated PDF is served inline/downloadable and page overflow warnings are surfaced if page count exceeds the configured limit
