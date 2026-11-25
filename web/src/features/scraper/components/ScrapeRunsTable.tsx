import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { RUN_STATUS } from '@/lib/constants';
import type { RunsOverviewResponse } from '@/types';

/**
 * Table displaying recent `scrape_runs` execution metrics and statuses.
 */
export function ScrapeRunsTable({ runs }: { runs: RunsOverviewResponse['runs'] }) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-zinc-100 px-4 py-3 text-xs font-semibold text-zinc-800">
        Recent Scrape Runs
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-zinc-100 bg-zinc-50/70 text-[11px] text-zinc-500">
            <tr>
              <th className="px-4 py-2">ID</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Providers</th>
              <th className="px-4 py-2">Fetched</th>
              <th className="px-4 py-2">New</th>
              <th className="px-4 py-2">Approved</th>
              <th className="px-4 py-2">Rejected</th>
              <th className="px-4 py-2">Started</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {runs.map(run => (
              <tr key={run.id} className="hover:bg-zinc-50">
                <td className="px-4 py-2.5 font-mono text-zinc-500">#{run.id}</td>
                <td className="px-4 py-2.5">
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
                </td>
                <td className="px-4 py-2.5 text-zinc-600">{run.providers.join(', ') || '—'}</td>
                <td className="px-4 py-2.5 font-mono">{run.total_fetched}</td>
                <td className="px-4 py-2.5 font-mono">{run.total_new}</td>
                <td className="px-4 py-2.5 font-mono text-emerald-700">{run.total_approved}</td>
                <td className="px-4 py-2.5 font-mono text-zinc-500">{run.total_rejected}</td>
                <td className="px-4 py-2.5 font-mono text-[11px] text-zinc-400">
                  {new Date(run.started_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
