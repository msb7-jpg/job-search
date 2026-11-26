import { useEventListener } from '@reactuses/core';
import { FORM_INPUT_TAGS, JOB_STATUS, type JobStatus, KEY_NAME } from '@/lib/constants';
import { studioJobIdSignal } from '@/state/signals';

/** Parameters for the triage keyboard shortcut listener. */
interface UseTriageKeyboardParams {
  /** Currently focused job ID in the inbox, or `null`. */
  selectedJobId: number | null;
  /** External posting URL of the selected job. */
  selectedJobUrl: string | undefined;
  /** Callback to move selection up (`-1`) or down (`+1`). */
  onMoveSelection: (delta: number) => void;
  /** Callback to save or ignore the currently selected job. */
  onStatusAction: (status: Extract<JobStatus, 'SAVED' | 'IGNORED'>) => void;
}

/**
 * Binds `J`/`K`/`S`/`X`/`T`/`O` keyboard shortcuts for rapid inbox triage.
 */
export function useTriageKeyboard({
  selectedJobId,
  selectedJobUrl,
  onMoveSelection,
  onStatusAction,
}: UseTriageKeyboardParams) {
  useEventListener('keydown', (event: KeyboardEvent) => {
    const targetTag = (event.target as HTMLElement)?.tagName;
    const isTypingInInput = FORM_INPUT_TAGS.includes(
      targetTag as (typeof FORM_INPUT_TAGS)[number]
    );
    const isReviewStudioOpen = studioJobIdSignal.value !== null;

    if (isTypingInInput || isReviewStudioOpen) {
      return;
    }

    const actions = new Map<string, () => void>([
      [KEY_NAME.NEXT, () => onMoveSelection(1)],
      [KEY_NAME.PREV, () => onMoveSelection(-1)],
      [KEY_NAME.SAVE, () => onStatusAction(JOB_STATUS.SAVED)],
      [KEY_NAME.IGNORE, () => onStatusAction(JOB_STATUS.IGNORED)],
      [
        KEY_NAME.TAILOR,
        () => {
          if (selectedJobId !== null) studioJobIdSignal.value = selectedJobId;
        },
      ],
      [
        KEY_NAME.OPEN,
        () => {
          if (selectedJobUrl) window.open(selectedJobUrl, '_blank', 'noopener,noreferrer');
        },
      ],
    ]);

    const action = actions.get(event.key.toLowerCase());
    if (action) {
      event.preventDefault();
      action();
    }
  });
}
