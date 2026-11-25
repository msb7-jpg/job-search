import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn, formatRelativeDate } from '@/lib/utils';
import type { JobSummary } from '@/types';

/** Props for the left-hand Triage Inbox job list. */
interface InboxListProps {
  /** Qualified `NEW` jobs to render. */
  jobs: JobSummary[];
  /** Whether the initial inbox query is loading. */
  isLoading: boolean;
  /** Currently selected job ID. */
  selectedId: number | null;
  /** Callback invoked when a user clicks a job row. */
  onSelectJob: (jobId: number) => void;
}

/**
 * Compact scrollable list of qualified jobs in the Triage Inbox split pane.
 */
export function InboxList({ jobs, isLoading, selectedId, onSelectJob }: InboxListProps) {
  return (
    <Card className="flex min-h-0 flex-col overflow-hidden lg:col-span-5">
      <div className="flex items-center justify-between border-b border-zinc-100 px-3.5 py-2.5">
        <span className="text-xs font-medium text-zinc-700">Qualified Inbox</span>
        <Badge variant="mint" className="font-mono">
          {jobs.length} new
        </Badge>
      </div>
      <div className="flex-1 divide-y divide-zinc-100 overflow-y-auto">
        {isLoading ? (
          <div className="p-6 text-center text-xs text-zinc-400">Loading inbox...</div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-xs text-zinc-400">
            Inbox zero. Run a scrape or check your Application Tracker.
          </div>
        ) : (
          jobs.map(job => {
            const isSelected = job.id === selectedId;
            const score = job.evaluation?.llm_score || job.evaluation?.layer1_score || 0;
            return (
              <button
                key={job.id}
                type="button"
                onClick={() => onSelectJob(job.id)}
                className={cn(
                  'w-full text-left px-3.5 py-3 transition-colors cursor-pointer',
                  isSelected
                    ? 'bg-emerald-50/70 border-l-2 border-l-emerald-600'
                    : 'hover:bg-zinc-50'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-semibold text-zinc-900">{job.title}</div>
                    <div className="mt-0.5 flex items-center gap-1.5 text-[11px] text-zinc-500">
                      <span className="truncate font-medium text-zinc-700">{job.company}</span>
                      <span>•</span>
                      <span>{job.provider}</span>
                    </div>
                  </div>
                  <Badge variant={score >= 80 ? 'mint' : 'neutral'} className="font-mono shrink-0">
                    {score}%
                  </Badge>
                </div>
                <div className="mt-2 flex items-center gap-2 text-[11px] text-zinc-400">
                  <span>{job.work_model}</span>
                  <span>•</span>
                  <span>{job.seniority}</span>
                  <span className="ml-auto font-mono">
                    {formatRelativeDate(job.first_seen_at)}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </Card>
  );
}
