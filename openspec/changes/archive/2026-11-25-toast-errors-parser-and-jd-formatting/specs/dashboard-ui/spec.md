# Delta Specification: Dashboard UI

## MODIFIED Requirements

### Requirement: Feature-Folder Orchestration and Reactive State
`App.tsx` and feature `*Page.tsx` / `ReviewStudioModal.tsx` MUST act as thin orchestrators (`<= 120` lines) using Preact Signals, TanStack Query v5, TanStack Table v8, and `@dnd-kit`. `ToastBanner` MUST render high-contrast error and success notifications in a clearly visible screen position, and `FormattedDescription` MUST render structured job descriptions with preserved headings, paragraphs, and lists.

#### Scenario: Top-level Command Center navigation
- **WHEN** the user switches between `Inbox`, `Tracker`, `Audit Log`, `Scraper`, `Profile`, and `Settings` in `App.tsx`
- **THEN** `activeTabSignal` renders the corresponding feature view and displays a pending badge on `Scraper` when `pending_llm_count > 0`

#### Scenario: Displaying error vs success toasts
- **WHEN** a mutation fails (e.g., empty `MasterProfile` on tailor)
- **THEN** `toastSignal` receives `variant: 'error'` and `ToastBanner` renders with high-contrast error styling
