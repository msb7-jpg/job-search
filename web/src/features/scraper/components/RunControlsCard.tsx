import { Play, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

/** Props for the scraper provider selection and run control card. */
interface RunControlsCardProps {
  /** All active provider names registered in the backend. */
  availableProviders: string[];
  /** Currently selected provider names to scrape. */
  selectedProviders: string[];
  /** Whether the proxy pool is enabled for the next run. */
  useProxy: boolean;
  /** Whether the Layer 2 LLM Judge is enabled for the next run. */
  useLlm: boolean;
  /** Whether a background run is currently active. */
  isRunning: boolean;
  /** Whether the trigger request is in flight. */
  isTriggerPending: boolean;
  /** Number of jobs awaiting `PENDING` LLM evaluation. */
  pendingLlmCount: number;
  /** Toggles a provider in or out of `selectedProviders`. */
  onToggleProvider: (name: string) => void;
  /** Toggles proxy pool usage. */
  onToggleProxy: (checked: boolean) => void;
  /** Toggles LLM Judge usage. */
  onToggleLlm: (checked: boolean) => void;
  /** Starts a new background scrape run. */
  onTriggerRun: () => void;
  /** Starts a background rejudge run for `PENDING` jobs. */
  onTriggerRejudge: () => void;
}

/**
 * Control panel card for selecting providers and triggering scrape or rejudge runs.
 */
export function RunControlsCard({
  availableProviders,
  selectedProviders,
  useProxy,
  useLlm,
  isRunning,
  isTriggerPending,
  pendingLlmCount,
  onToggleProvider,
  onToggleProxy,
  onToggleLlm,
  onTriggerRun,
  onTriggerRejudge,
}: RunControlsCardProps) {
  return (
    <Card className="p-4 space-y-4 lg:col-span-5">
      <div>
        <h2 className="text-sm font-semibold text-zinc-900">Pipeline Controls</h2>
        <p className="text-xs text-zinc-500">
          Select active providers and run concurrent scraping + SQLite dedup + LLM Judge.
        </p>
      </div>

      <div className="space-y-2">
        <div className="text-[11px] font-medium uppercase tracking-wider text-zinc-400">
          Providers
        </div>
        <div className="flex flex-wrap gap-2">
          {availableProviders.map(prov => {
            const isActive = selectedProviders.includes(prov);
            return (
              <button
                key={prov}
                type="button"
                onClick={() => onToggleProvider(prov)}
                className={`rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                  isActive
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                    : 'border-zinc-200 bg-white text-zinc-500 hover:bg-zinc-50'
                }`}
              >
                {prov}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap gap-4 text-xs text-zinc-700">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useProxy}
            onChange={event => onToggleProxy(event.target.checked)}
            className="accent-emerald-600"
          />
          Use Proxy Pool
        </label>
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useLlm}
            onChange={event => onToggleLlm(event.target.checked)}
            className="accent-emerald-600"
          />
          Use LLM Judge
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <Button variant="primary" disabled={isRunning || isTriggerPending} onClick={onTriggerRun}>
          <Play className="h-3.5 w-3.5" />
          {isRunning ? 'Running...' : 'Run Scrape Now'}
        </Button>

        <Button
          variant="outline"
          disabled={isRunning || pendingLlmCount === 0}
          onClick={onTriggerRejudge}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry Pending LLM ({pendingLlmCount})
        </Button>
      </div>
    </Card>
  );
}
