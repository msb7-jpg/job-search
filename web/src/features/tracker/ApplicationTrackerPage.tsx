import { useSignal } from '@preact/signals-react';
import { useQuery } from '@tanstack/react-query';
import { Kanban, Table as TableIcon } from 'lucide-react';
import { useUpdateJobStatus } from '@/api/mutations';
import { jobQueries } from '@/api/queries';
import { Button } from '@/components/ui/button';
import { JOB_STATUS, TRACKER_VIEW_MODE } from '@/lib/constants';
import { showToast, studioJobIdSignal } from '@/state/signals';
import type { ApplicationStatus, JobSummary } from '@/types';
import { KanbanBoard } from './components/KanbanBoard';
import { NotesModal } from './components/NotesModal';
import { TrackerTable } from './components/TrackerTable';

const TRACKED_STATUSES = [
  JOB_STATUS.SAVED,
  JOB_STATUS.TAILORING,
  JOB_STATUS.READY_TO_APPLY,
  JOB_STATUS.APPLIED,
  JOB_STATUS.INTERVIEWING,
  JOB_STATUS.OFFER,
].join(',');

/**
 * Page orchestrator for tracking applications across Kanban and Table views.
 */
export function ApplicationTrackerPage() {
  const viewMode = useSignal<
    typeof TRACKER_VIEW_MODE.KANBAN | typeof TRACKER_VIEW_MODE.TABLE
  >(TRACKER_VIEW_MODE.KANBAN);
  const editingNotesJob = useSignal<JobSummary | null>(null);

  const query = useQuery(jobQueries.list({ status: TRACKED_STATUSES, limit: 250 }));
  const jobs = query.data?.items ?? [];
  const updateStatus = useUpdateJobStatus();

  const handleMoveStatus = (jobId: number, status: ApplicationStatus) => {
    updateStatus.mutate({ jobId, status }, { onSuccess: () => showToast(`Moved to ${status}`) });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">Application Tracker</h2>
          <p className="text-xs text-zinc-500">
            Drag cards across stages or switch to table view for bulk updates.
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-zinc-200 bg-white p-0.5">
          <Button
            variant={viewMode.value === TRACKER_VIEW_MODE.KANBAN ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => {
              viewMode.value = TRACKER_VIEW_MODE.KANBAN;
            }}
          >
            <Kanban className="h-3.5 w-3.5" />
            Kanban
          </Button>
          <Button
            variant={viewMode.value === TRACKER_VIEW_MODE.TABLE ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => {
              viewMode.value = TRACKER_VIEW_MODE.TABLE;
            }}
          >
            <TableIcon className="h-3.5 w-3.5" />
            Table
          </Button>
        </div>
      </div>

      {viewMode.value === TRACKER_VIEW_MODE.KANBAN ? (
        <KanbanBoard
          jobs={jobs}
          onMoveStatus={handleMoveStatus}
          onTailor={jobId => {
            studioJobIdSignal.value = jobId;
          }}
          onSelectNotes={job => {
            editingNotesJob.value = job;
          }}
        />
      ) : (
        <TrackerTable
          jobs={jobs}
          onMoveStatus={handleMoveStatus}
          onSelectNotes={job => {
            editingNotesJob.value = job;
          }}
          onTailor={jobId => {
            studioJobIdSignal.value = jobId;
          }}
        />
      )}

      {editingNotesJob.value && (
        <NotesModal
          job={editingNotesJob.value}
          onClose={() => {
            editingNotesJob.value = null;
          }}
          onSave={notes => {
            const targetJob = editingNotesJob.value;
            if (!targetJob) return;
            updateStatus.mutate(
              {
                jobId: targetJob.id,
                status: targetJob.application?.status ?? JOB_STATUS.SAVED,
                notes,
              },
              {
                onSuccess: () => {
                  showToast('Notes saved');
                  editingNotesJob.value = null;
                },
              }
            );
          }}
        />
      )}
    </div>
  );
}
