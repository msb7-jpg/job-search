import { APP_TAB, TRACKER_VIEW_MODE } from '@/lib/constants';
import type { AppTab } from './signals';

/** Valid Tracker display modes synchronized with URL `?view=`. */
export type TrackerViewMode = 'kanban' | 'table';

/** Snapshot of UI navigation state persisted in URL query parameters. */
export interface UrlNavigationState {
  /** Active top-level Command Center tab. */
  tab: AppTab;
  /** Selected job ID in the Triage Inbox, or `null`. */
  selectedJobId: number | null;
  /** Job ID open in Review Studio, or `null`. */
  studioJobId: number | null;
  /** Display mode for the Application Tracker. */
  trackerView: TrackerViewMode;
  /** Selected historical scrape run ID in Scraper Control, or `null`. */
  historyRunId: number | null;
}

const VALID_TABS = new Set<string>(Object.values(APP_TAB));

/** Parses a strictly positive integer query parameter, returning `null` if invalid. */
function parsePositiveInt(rawValue: string | null): number | null {
  if (!rawValue) return null;
  const parsed = Number.parseInt(rawValue, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

/**
 * Reads navigation state from `window.location.search`, falling back to safe defaults.
 */
export function readUrlState(): UrlNavigationState {
  if (typeof window === 'undefined') {
    return {
      tab: APP_TAB.TRIAGE,
      selectedJobId: null,
      studioJobId: null,
      trackerView: TRACKER_VIEW_MODE.KANBAN,
      historyRunId: null,
    };
  }
  const params = new URLSearchParams(window.location.search);
  const rawTab = params.get('tab');
  const tab = rawTab && VALID_TABS.has(rawTab) ? (rawTab as AppTab) : APP_TAB.TRIAGE;
  const rawView = params.get('view');
  const trackerView =
    rawView === TRACKER_VIEW_MODE.TABLE ? TRACKER_VIEW_MODE.TABLE : TRACKER_VIEW_MODE.KANBAN;

  return {
    tab,
    selectedJobId: parsePositiveInt(params.get('job')),
    studioJobId: parsePositiveInt(params.get('studio')),
    trackerView,
    historyRunId: parsePositiveInt(params.get('run')),
  };
}

/** Appends a query parameter only when `condition` holds and `value` is non-null. */
function setConditionalParam(
  params: URLSearchParams,
  key: string,
  value: string | number | null,
  condition = true
): void {
  if (condition && value !== null) {
    params.set(key, String(value));
  }
}

/** Encodes active navigation fields into a normalized URL search string. */
function buildSearchString(state: UrlNavigationState): string {
  const params = new URLSearchParams();
  setConditionalParam(params, 'tab', state.tab, state.tab !== APP_TAB.TRIAGE);
  setConditionalParam(params, 'job', state.selectedJobId, state.tab === APP_TAB.TRIAGE);
  setConditionalParam(params, 'studio', state.studioJobId);
  setConditionalParam(
    params,
    'view',
    state.trackerView,
    state.tab === APP_TAB.TRACKER && state.trackerView !== TRACKER_VIEW_MODE.KANBAN
  );
  setConditionalParam(params, 'run', state.historyRunId, state.tab === APP_TAB.SCRAPER);
  const query = params.toString();
  return query ? `?${query}` : '';
}

/**
 * Synchronizes the browser query string with the current navigation signals without reloading.
 */
export function syncUrlState(state: UrlNavigationState): void {
  if (typeof window === 'undefined') return;
  const nextSearch = buildSearchString(state);
  if (window.location.search === nextSearch) return;
  window.history.replaceState(null, '', `${window.location.pathname}${nextSearch}${window.location.hash}`);
}
