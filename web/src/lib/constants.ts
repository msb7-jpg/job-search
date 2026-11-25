/**
 * Top-level navigation tabs in the Command Center shell.
 */
export const APP_TAB = {
  TRIAGE: 'triage',
  TRACKER: 'tracker',
  REJECTIONS: 'rejections',
  SCRAPER: 'scraper',
  PROFILE: 'profile',
  SETTINGS: 'settings',
} as const;

/**
 * Application workflow statuses matching the backend SQLite enum.
 */
export const JOB_STATUS = {
  NEW: 'NEW',
  SAVED: 'SAVED',
  TAILORING: 'TAILORING',
  READY_TO_APPLY: 'READY_TO_APPLY',
  APPLIED: 'APPLIED',
  INTERVIEWING: 'INTERVIEWING',
  OFFER: 'OFFER',
  REJECTED: 'REJECTED',
  IGNORED: 'IGNORED',
} as const;

/** A valid application workflow status. */
export type JobStatus = (typeof JOB_STATUS)[keyof typeof JOB_STATUS];

/**
 * LLM evaluation statuses persisted in `job_evaluations`.
 */
export const LLM_STATUS = {
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
  SKIPPED: 'SKIPPED',
  PENDING: 'PENDING',
} as const;

/**
 * Scrape run lifecycle statuses.
 */
export const RUN_STATUS = {
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  RUNNING: 'RUNNING',
} as const;

/**
 * Tracker display modes.
 */
export const TRACKER_VIEW_MODE = {
  KANBAN: 'kanban',
  TABLE: 'table',
} as const;

/**
 * Server-Sent Event payload types emitted by `/api/runs/{id}/stream`.
 */
export const SSE_EVENT_TYPE = {
  LOG: 'log',
  DONE: 'done',
} as const;

/**
 * Verification warning types emitted by `verify_tailored_diff` and `pypdf`.
 */
export const WARNING_TYPE = {
  OVERFLOW_PAGES: 'overflow_pages',
  NEW_NUMBER: 'new_number',
  UNKNOWN_BULLET_ID: 'unknown_bullet_id',
} as const;

/**
 * Keyboard keys used for triage shortcuts and input submissions.
 */
export const KEY_NAME = {
  ENTER: 'Enter',
  NEXT: 'j',
  PREV: 'k',
  SAVE: 's',
  IGNORE: 'x',
  TAILOR: 't',
  OPEN: 'o',
} as const;

/**
 * HTML element tag names ignored by global keyboard shortcuts.
 */
export const FORM_INPUT_TAGS = ['INPUT', 'TEXTAREA', 'SELECT'] as const;

/**
 * Visual variants for transient toast notifications.
 */
export const TOAST_VARIANT = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info',
} as const;
