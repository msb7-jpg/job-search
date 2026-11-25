import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/DataTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { JOB_STATUS } from '@/lib/constants';
import type { ApplicationStatus, JobSummary } from '@/types';
import { KANBAN_COLUMNS } from '../constants';

/** Props for the tabular view of tracked applications. */
interface TrackerTableProps {
  /** Tracked application jobs to display. */
  jobs: JobSummary[];
  /** Updates a job's application stage. */
  onMoveStatus: (jobId: number, status: ApplicationStatus) => void;
  /** Opens the notes modal for a job. */
  onSelectNotes: (job: JobSummary) => void;
  /** Opens the Review Studio modal for a job. */
  onTailor: (jobId: number) => void;
}

/**
 * Tabular alternative to the Kanban board using TanStack Table v8.
 */
export function TrackerTable({
  jobs,
  onMoveStatus,
  onSelectNotes,
  onTailor,
}: TrackerTableProps) {
  const columns: ColumnDef<JobSummary>[] = [
    {
      accessorKey: 'title',
      header: 'Role',
      cell: ({ row }) => (
        <div>
          <div className="font-medium text-zinc-900">{row.original.title}</div>
          <div className="text-[11px] text-zinc-500">{row.original.company}</div>
        </div>
      ),
    },
    {
      accessorKey: 'provider',
      header: 'Source',
      cell: ({ row }) => <Badge variant="outline">{row.original.provider}</Badge>,
    },
    {
      id: 'status',
      header: 'Stage',
      cell: ({ row }) => (
        <select
          value={row.original.application?.status ?? JOB_STATUS.SAVED}
          onChange={event =>
            onMoveStatus(row.original.id, event.target.value as ApplicationStatus)
          }
          className="h-7 rounded-md border border-zinc-200 bg-white px-2 text-xs"
        >
          {KANBAN_COLUMNS.map(col => (
            <option key={col.id} value={col.id}>
              {col.label}
            </option>
          ))}
        </select>
      ),
    },
    {
      id: 'notes',
      header: 'Notes',
      cell: ({ row }) => (
        <button
          type="button"
          onClick={() => onSelectNotes(row.original)}
          className="max-w-xs truncate text-left text-xs text-zinc-600 hover:text-emerald-700 cursor-pointer"
        >
          {row.original.application?.notes || 'Add note...'}
        </button>
      ),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button variant="outline" size="sm" onClick={() => onTailor(row.original.id)}>
            Tailor
          </Button>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={jobs}
      searchColumn="title"
      searchPlaceholder="Filter tracked applications..."
    />
  );
}
