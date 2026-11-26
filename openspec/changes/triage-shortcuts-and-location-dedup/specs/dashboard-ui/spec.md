# Delta Specification: Dashboard UI

## MODIFIED Requirements

### Requirement: Feature-Folder Orchestration and Reactive State
`App.tsx` and feature `*Page.tsx` / `ReviewStudioModal.tsx` MUST act as thin orchestrators (`<= 120` lines) using Preact Signals, TanStack Query v5, TanStack Table v8, and `@dnd-kit`. `ToastBanner` MUST render high-contrast error and success notifications, `FormattedDescription` MUST render structured job descriptions, triage action buttons (`Tailor`, `Save`, `Ignore`, `Blacklist`, `Open`) MUST render clean labels with keyboard shortcuts in hover tooltips, and location lists MUST split and deduplicate comma-separated entries.

#### Scenario: Top-level Command Center navigation
- **WHEN** the user switches between `Inbox`, `Tracker`, `Audit Log`, `Scraper`, `Profile`, and `Settings` in `App.tsx`
- **THEN** `activeTabSignal` renders the corresponding feature view and displays a pending badge on `Scraper` when `pending_llm_count > 0`

#### Scenario: Displaying error vs success toasts
- **WHEN** a mutation fails (e.g., empty `MasterProfile` on tailor)
- **THEN** `toastSignal` receives `variant: 'error'` and `ToastBanner` renders with high-contrast error styling

#### Scenario: Hovering triage action button
- **WHEN** the user hovers over `Tailor`, `Save`, `Ignore`, `Blacklist`, or `Open`
- **THEN** a tooltip displays the corresponding keyboard shortcut (`T`, `S`, `X`, etc.)

#### Scenario: Displaying multi-location job
- **WHEN** a job's `location` / `other_locations` contains comma-separated or repeated regions
- **THEN** the UI splits and deduplicates them before rendering
