import type { ColumnDef } from '@tanstack/react-table';
import { Ban, RotateCcw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { JobSummary } from '@/types';

/**
 * Builds TanStack Table column definitions for the Rejection Audit Log.
 */
export function buildRejectionColumns(
  onRescue: (jobId: number) => void,
  onBlacklist: (companyName: string) => void
): ColumnDef<JobSummary>[] {
  return [
    {
      accessorKey: 'title',
      header: 'Role & Company',
      cell: ({ row }) => (
        <div className="max-w-xs">
          <a
            href={row.original.url}
            target="_blank"
            rel="noreferrer"
            className="font-medium text-zinc-900 hover:text-emerald-700 hover:underline"
          >
            {row.original.title}
          </a>
          <div className="text-[11px] text-zinc-500">
            {row.original.company} • {row.original.provider}
          </div>
        </div>
      ),
    },
    {
      id: 'discard_layer',
      header: 'Discard Layer',
      cell: ({ row }) => (
        <Badge variant="amber">
          {row.original.evaluation?.discard_layer ||
            row.original.evaluation?.llm_status ||
            'Rejected'}
        </Badge>
      ),
    },
    {
      id: 'discard_reason',
      header: 'Reason',
      cell: ({ row }) => (
        <p className="max-w-md text-xs text-zinc-600">
          {row.original.evaluation?.discard_reason ||
            row.original.evaluation?.llm_reasoning ||
            '—'}
        </p>
      ),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button variant="outline" size="sm" onClick={() => onRescue(row.original.id)}>
            <RotateCcw className="h-3 w-3 text-emerald-600" />
            Rescue
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onBlacklist(row.original.company)}
            title="Blacklist company"
          >
            <Ban className="h-3 w-3 text-red-500" />
          </Button>
        </div>
      ),
    },
  ];
}
