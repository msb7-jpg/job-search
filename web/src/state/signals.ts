import { signal } from '@preact/signals-react';
import { APP_TAB, TOAST_VARIANT } from '@/lib/constants';

/** Union of valid top-level navigation tab identifiers. */
export type AppTab = (typeof APP_TAB)[keyof typeof APP_TAB];

/** Visual severity variant for toast notifications. */
export type ToastVariant = (typeof TOAST_VARIANT)[keyof typeof TOAST_VARIANT];

/** Payload for the active toast notification. */
export interface ToastPayload {
  /** Human-readable notification text. */
  message: string;
  /** Visual variant controlling color and icon. */
  variant: ToastVariant;
}

/** Active navigation tab in the Command Center shell. */
export const activeTabSignal = signal<AppTab>(APP_TAB.TRIAGE);

/** Currently selected job ID in the Triage Inbox split pane. */
export const selectedJobIdSignal = signal<number | null>(null);

/** Job ID currently open in the Review Studio modal, or `null` when closed. */
export const studioJobIdSignal = signal<number | null>(null);

/** Active background scrape/rejudge run ID streaming logs via SSE. */
export const activeRunIdSignal = signal<string | null>(null);

/** Rolling buffer of live log lines received from the SSE run stream. */
export const sseLogsSignal = signal<string[]>([]);

/** Transient toast notification shown at the top-right corner. */
export const toastSignal = signal<ToastPayload | null>(null);

/**
 * Displays a transient toast notification for 4.5 seconds.
 */
export function showToast(message: string, variant: ToastVariant = TOAST_VARIANT.SUCCESS) {
  toastSignal.value = { message, variant };
  window.setTimeout(() => {
    if (toastSignal.value?.message === message) {
      toastSignal.value = null;
    }
  }, 4500);
}
