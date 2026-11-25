import { JOB_STATUS } from '@/lib/constants';
import type { ApplicationStatus } from '@/types';

/**
 * Ordered Kanban columns for the Application Tracker.
 */
export const KANBAN_COLUMNS: { id: ApplicationStatus; label: string }[] = [
  { id: JOB_STATUS.SAVED, label: 'Saved' },
  { id: JOB_STATUS.TAILORING, label: 'Tailoring' },
  { id: JOB_STATUS.READY_TO_APPLY, label: 'Ready' },
  { id: JOB_STATUS.APPLIED, label: 'Applied' },
  { id: JOB_STATUS.INTERVIEWING, label: 'Interviewing' },
  { id: JOB_STATUS.OFFER, label: 'Offer' },
];
