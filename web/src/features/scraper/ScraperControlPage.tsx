import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { sseLogsSignal } from '@/state/signals';
import { LiveLogConsole } from './components/LiveLogConsole';
import { RunControlsCard } from './components/RunControlsCard';
import { ScrapeRunsTable } from './components/ScrapeRunsTable';
import { useScraperActions } from './hooks/useScraperActions';

/**
 * Page orchestrator for scraper controls, live SSE logs, and run history.
 */
export function ScraperControlPage() {
  const scraper = useScraperActions();
  const pendingCount = scraper.overview?.pending_llm_count ?? 0;

  return (
    <div className="space-y-4">
      {pendingCount > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-300 bg-amber-50/90 px-4 py-3 text-xs text-amber-950">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
            <span>
              <strong className="font-semibold">{pendingCount}</strong> job(s) are waiting in{' '}
              <code className="font-mono font-semibold">PENDING</code> for LLM evaluation.
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={scraper.isRunning}
            onClick={scraper.triggerRejudge}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Evaluate Pending Now
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <RunControlsCard
          availableProviders={scraper.overview?.available_providers ?? []}
          selectedProviders={scraper.selectedProviders}
          useProxy={scraper.useProxy}
          useLlm={scraper.useLlm}
          isRunning={scraper.isRunning}
          isTriggerPending={scraper.isTriggerPending}
          pendingLlmCount={pendingCount}
          onToggleProvider={scraper.toggleProvider}
          onToggleProxy={scraper.setUseProxy}
          onToggleLlm={scraper.setUseLlm}
          onTriggerRun={scraper.triggerRun}
          onTriggerRejudge={scraper.triggerRejudge}
        />
        <LiveLogConsole logs={sseLogsSignal.value} isRunning={scraper.isRunning} />
      </div>

      <ScrapeRunsTable runs={scraper.overview?.runs ?? []} />
    </div>
  );
}
