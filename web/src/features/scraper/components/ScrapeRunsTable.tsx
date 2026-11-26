import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { RUN_STATUS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { RunsOverviewResponse } from '@/types';

/** Props for the recent scrape runs history table. */
interface ScrapeRunsTableProps {
  /** Recent scrape runs ordered newest first. */
  runs: RunsOverviewResponse['runs'];
  /** Currently selected run ID whose logs are displayed, or `null`. */
  selectedRunId: number | null;
  /** Callback fired when a run row is clicked to inspect its logs. */
  onSelectRun: (runId: number) => void;
}

/**
 * Table displaying recent `scrape_runs` execution metrics; clicking a row inspects its persisted logs.
 */
export function ScrapeRunsTable({ runs, selectedRunId, onSelectRun }: ScrapeRunsTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
        <span className="text-xs font-semibold text-zinc-800">Recent Scrape Runs</span>
        <span className="text-[11px] text-zinc-400">Click a row to inspect logs</span>
      </div>
      <Table className="text-xs">
        <TableHeader className="bg-zinc-50/70 text-[11px] text-zinc-500">
          <TableRow>
            <TableHead className="px-4 py-2">ID</TableHead>
            <TableHead className="px-4 py-2">Status</TableHead>
            <TableHead className="px-4 py-2">Providers</TableHead>
            <TableHead className="px-4 py-2">Fetched</TableHead>
            <TableHead className="px-4 py-2">New</TableHead>
            <TableHead className="px-4 py-2">Approved</TableHead>
            <TableHead className="px-4 py-2">Rejected</TableHead>
            <TableHead className="px-4 py-2">Started</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map(run => {
            const isSelected = selectedRunId === run.id;
            return (
              <TableRow
                key={run.id}
                onClick={() => onSelectRun(run.id)}
                className={cn(
                  'cursor-pointer',
                  isSelected && 'bg-emerald-50/70 hover:bg-emerald-50'
                )}
              >
                <TableCell className="px-4 py-2.5 font-mono text-zinc-500">#{run.id}</TableCell>
                <TableCell className="px-4 py-2.5">
                  <Badge
                    variant={
                      run.status === RUN_STATUS.COMPLETED
                        ? 'mint'
                        : run.status === RUN_STATUS.FAILED
                        ? 'danger'
                        : 'amber'
                    }
                  >
                    {run.status}
                  </Badge>
                </TableCell>
                <TableCell className="px-4 py-2.5 text-zinc-600">
                  {run.providers.join(', ') || '—'}
                </TableCell>
                <TableCell className="px-4 py-2.5 font-mono">{run.total_fetched}</TableCell>
                <TableCell className="px-4 py-2.5 font-mono">{run.total_new}</TableCell>
                <TableCell className="px-4 py-2.5 font-mono text-emerald-700">
                  {run.total_approved}
                </TableCell>
                <TableCell className="px-4 py-2.5 font-mono text-zinc-500">
                  {run.total_rejected}
                </TableCell>
                <TableCell className="px-4 py-2.5 font-mono text-[11px] text-zinc-400">
                  {new Date(run.started_at).toLocaleString()}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Card>
  );
}
