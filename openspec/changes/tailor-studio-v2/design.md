# Design

## Open Questions (Resolve via `/openspec-explore` before apply)
- Which exact ATS/section score dimensions (`Keyword Match`, `Skills Alignment`, `Experience Relevance`, `Qualifications Match`, `Formatting & Readability`) are computed deterministically vs by LLM?
- Should `academic_experiences` / `monitorias` be a dedicated `MasterProfile` list or entries in `EducationEntry.highlights` / typed `ExperienceEntry`?
- Should live tailoring progress stream over SSE or step-by-step backend state?

## Approach
1. Update `MasterProfile`, `parse_resume_with_llm()`, and `resume.html.j2` to preserve academic experiences & monitorias and raise `renderer.py` page limit to 2.
2. Refactor `ReviewStudioModal.tsx` into a translucent shadcn `Dialog` (`backdrop-blur`), extracting step-progress, diff-highlight, ATS-score, and JD-popup child components (`<= 200` lines each).

## Verification
- Unit tests for 2-page guardrail and academic experience parsing.
- `make check` exits `0`.
