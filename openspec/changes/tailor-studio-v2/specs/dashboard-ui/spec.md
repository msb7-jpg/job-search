# Delta Specification: Dashboard UI

## MODIFIED Requirements

### Requirement: Feature-Folder Orchestration and Reactive State
`App.tsx` and feature `*Page.tsx` / `ReviewStudioModal.tsx` MUST act as thin orchestrators (`<= 120` lines) using Preact Signals, TanStack Query v5, TanStack Table v8, and `@dnd-kit`. `ToastBanner` MUST render high-contrast error and success notifications in a clearly visible screen position, `FormattedDescription` MUST render structured job descriptions, and `ReviewStudioModal` MUST render as a translucent modal dialog (not fullscreen) with reactive tailoring step states, inline before/after diff highlighting, ATS/section score breakdown, and an on-demand popup/drawer for the original Job Description.

#### Scenario: Top-level Command Center navigation
- **WHEN** the user switches between `Inbox`, `Tracker`, `Audit Log`, `Scraper`, `Profile`, and `Settings` in `App.tsx`
- **THEN** `activeTabSignal` renders the corresponding feature view and displays a pending badge on `Scraper` when `pending_llm_count > 0`

#### Scenario: Displaying error vs success toasts
- **WHEN** a mutation fails (e.g., empty `MasterProfile` on tailor)
- **THEN** `toastSignal` receives `variant: 'error'` and `ToastBanner` renders with high-contrast error styling

#### Scenario: Live tailoring progress and diff review
- **WHEN** the user triggers CV tailoring for a job
- **THEN** the dialog displays live step-by-step progress and, once complete, highlights exact before/after diffs alongside ATS/section scores while keeping the original JD accessible via a popup
