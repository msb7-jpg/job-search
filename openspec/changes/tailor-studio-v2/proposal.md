# Proposal

## Why
The current Review Studio (`ReviewStudioModal.tsx`) is a static fullscreen view that hides tailoring progress, doesn't clearly highlight what changed from the base resume, keeps the full job description permanently occupying space, enforces a 1-page PDF limit instead of 2 pages, and ignores academic experiences/monitorias during resume parsing and tailoring.

## What Changes
- Replace the fullscreen Review Studio with a slightly translucent modal dialog (`ReviewStudioModal`) featuring live reactive step-by-step progress (Reading resume -> Analyzing job offer -> Matching -> Rewriting, inspired by `notes/tailor-cv-ui-example.png`).
- Add clear before/after diff highlighting so only modified bullets/summary stand out, and move the original Job Description into an on-demand popup/drawer instead of permanent split-pane space.
- Surface ATS match score overview and per-section score breakdowns (inspired by `notes/tailor-overview-and-options.png` and `notes/tailor-sections-score.png`).
- Raise the PDF page-count guardrail in `app/tailor/renderer.py` from 1 page to **2 pages**.
- Update `MasterProfile`, `app/tailor/parser.py`, and `resume.html.j2` to parse, store, and tailor academic experiences and monitorias (e.g., university coursework/degree & teaching assistantships).

## Capabilities

### Modified Capabilities
- `cv-tailoring`: Support 2-page PDF guardrail, academic experience/monitoria parsing and tailoring, and live tailoring progress/ATS section scoring.
- `dashboard-ui`: Translucent modal Review Studio with reactive step progress, inline before/after diff highlighting, on-demand JD popup, and ATS/section score cards.

## Impact
- Backend: `app/tailor/models.py`, `app/tailor/parser.py`, `app/tailor/service.py`, `app/tailor/renderer.py`, `app/tailor/templates/resume.html.j2`, `app/api/routers/tailor.py`.
- Frontend: `web/src/features/review/` (`ReviewStudioModal.tsx`, child components, hooks).
- References: `assets/tailor-cv-ui-example.png`, `assets/tailor-overview-and-options.png`, `assets/tailor-sections-score.png`.
