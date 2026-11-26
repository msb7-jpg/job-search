import { Terminal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

/** Props for the live SSE & historical run log console. */
interface LiveLogConsoleProps {
  /** Buffered log lines from the active stream or selected historical run. */
  logs: string[];
  /** Whether a run is currently streaming live events. */
  isRunning: boolean;
  /** Historical run ID being inspected, or `null` when viewing live stream. */
  historyRunId: number | null;
  /** Whether historical logs are currently loading. */
  isHistoryLoading: boolean;
  /** Callback to exit historical run inspection and return to the live stream. */
  onBackToLive: () => void;
}

/**
 * Monospace terminal console displaying real-time SSE logs or persisted historical run logs.
 */
export function LiveLogConsole({
  logs,
  isRunning,
  historyRunId,
  isHistoryLoading,
  onBackToLive,
}: LiveLogConsoleProps) {
  const emptyMessage = isHistoryLoading
    ? 'Loading run logs...'
    : historyRunId !== null
    ? 'No persisted logs recorded for this run.'
    : 'No active stream. Trigger a scrape or rejudge to watch live logs.';

  return (
    <Card className="flex flex-col overflow-hidden lg:col-span-7">
      <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-2.5">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-700">
          <Terminal className="h-3.5 w-3.5 text-emerald-600" />
          {historyRunId !== null ? `Run #${historyRunId} Logs` : 'Live Pipeline Stream'}
        </span>
        <div className="flex items-center gap-2">
          {historyRunId !== null && (
            <Button variant="ghost" size="xs" onClick={onBackToLive}>
              Back to Live
            </Button>
          )}
          {isRunning && historyRunId === null && <Badge variant="mint">LIVE</Badge>}
        </div>
      </div>
      <pre className="h-56 overflow-y-auto bg-zinc-950 p-3.5 font-mono text-[11px] leading-relaxed text-emerald-100">
        {logs.length > 0 ? logs.join('\n') : emptyMessage}
      </pre>
    </Card>
  );
}
