import { Terminal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

/** Props for the live SSE log console. */
interface LiveLogConsoleProps {
  /** Buffered log lines from the active or most recent run. */
  logs: string[];
  /** Whether a run is currently streaming live events. */
  isRunning: boolean;
}

/**
 * Monospace terminal console displaying real-time SSE logs from background runs.
 */
export function LiveLogConsole({ logs, isRunning }: LiveLogConsoleProps) {
  return (
    <Card className="flex flex-col overflow-hidden lg:col-span-7">
      <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-2.5">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-700">
          <Terminal className="h-3.5 w-3.5 text-emerald-600" />
          Live Pipeline Stream
        </span>
        {isRunning && <Badge variant="mint">LIVE</Badge>}
      </div>
      <pre className="h-56 overflow-y-auto bg-zinc-950 p-3.5 font-mono text-[11px] leading-relaxed text-emerald-100">
        {logs.length > 0
          ? logs.join('\n')
          : 'No active stream. Trigger a scrape or rejudge to watch live logs.'}
      </pre>
    </Card>
  );
}
