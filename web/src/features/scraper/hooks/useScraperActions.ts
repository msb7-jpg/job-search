import { useSignal } from '@preact/signals-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { runKeys, runQueries } from '@/api/queries';
import { TOAST_VARIANT } from '@/lib/constants';
import {
  activeRunIdSignal,
  selectedHistoryRunIdSignal,
  showToast,
  sseLogsSignal,
} from '@/state/signals';
import { useRunStream } from './useRunStream';

/** Extracts a readable error message from an unknown mutation error. */
function formatActionError(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

/** Toggles a provider name inside the selected provider list. */
function toggleProviderName(current: string[], name: string): string[] {
  return current.includes(name) ? current.filter(prov => prov !== name) : [...current, name];
}

/** Hooks the scrape trigger mutation with stream startup and toast feedback. */
function useTriggerRunMutation(
  onStarted: (runId: string, label: string) => void,
  selectedProviders: string[],
  useProxy: boolean,
  useLlm: boolean
) {
  return useMutation({
    mutationFn: () =>
      apiFetch<{ run_id: string }>('/api/runs/trigger', {
        method: 'POST',
        body: JSON.stringify({
          providers: selectedProviders.length > 0 ? selectedProviders : null,
          use_proxy: useProxy,
          use_llm: useLlm,
        }),
      }),
    onSuccess: res => onStarted(res.run_id, 'Started scrape run'),
    onError: err =>
      showToast(formatActionError(err, 'Failed to start scrape run'), TOAST_VARIANT.ERROR),
  });
}

/** Hooks the LLM rejudge mutation with stream startup and toast feedback. */
function useRejudgeRunMutation(onStarted: (runId: string, label: string) => void) {
  return useMutation({
    mutationFn: () => apiFetch<{ run_id: string }>('/api/runs/rejudge', { method: 'POST' }),
    onSuccess: res => onStarted(res.run_id, 'Started LLM rejudge'),
    onError: err =>
      showToast(formatActionError(err, 'Failed to start rejudge'), TOAST_VARIANT.ERROR),
  });
}

/** Resolves active providers, run ID, and running status from overview and signals. */
function resolveScraperStatus(
  override: string[] | null,
  availableProviders: string[] | undefined,
  overviewActiveRunId: string | null | undefined,
  overviewRunning: boolean | undefined
) {
  const activeSignalRunId = activeRunIdSignal.value;
  return {
    selectedProviders: override ?? availableProviders ?? [],
    effectiveActiveRunId: activeSignalRunId ?? overviewActiveRunId ?? null,
    isRunning: Boolean(overviewRunning || activeSignalRunId),
  };
}

/** Selects between historical run logs and live SSE logs for the console pane. */
function resolveConsoleLogs(historyRunId: number | null, historyLogs: string[] | undefined) {
  if (historyRunId === null) {
    return sseLogsSignal.value;
  }
  return historyLogs ?? [];
}

/**
 * Encapsulates scraper provider selection, run triggering, LLM rejudge,
 * live SSE reconnection on reload, and historical run log inspection.
 */
export function useScraperActions() {
  const queryClient = useQueryClient();
  const overview = useQuery(runQueries.overview()).data;

  const selectedProvidersOverride = useSignal<string[] | null>(null);
  const useProxy = useSignal(true);
  const useLlm = useSignal(true);

  const { selectedProviders, effectiveActiveRunId, isRunning } = resolveScraperStatus(
    selectedProvidersOverride.value,
    overview?.available_providers,
    overview?.active_run_id,
    overview?.is_running
  );
  useRunStream(effectiveActiveRunId);

  const historyRunId = selectedHistoryRunIdSignal.value;
  const historyLogsQuery = useQuery(runQueries.logs(historyRunId));

  const startStream = (runId: string, label: string) => {
    selectedHistoryRunIdSignal.value = null;
    sseLogsSignal.value = [`${label} ${runId}...`];
    activeRunIdSignal.value = runId;
    showToast(label);
    queryClient.invalidateQueries({ queryKey: runKeys.overview() });
  };

  const triggerMutation = useTriggerRunMutation(
    startStream,
    selectedProviders,
    useProxy.value,
    useLlm.value
  );
  const rejudgeMutation = useRejudgeRunMutation(startStream);

  return {
    overview,
    selectedProviders,
    useProxy: useProxy.value,
    useLlm: useLlm.value,
    isRunning,
    isTriggerPending: triggerMutation.isPending,
    historyRunId,
    isHistoryLoading: historyRunId !== null && historyLogsQuery.isLoading,
    consoleLogs: resolveConsoleLogs(historyRunId, historyLogsQuery.data?.logs),
    setUseProxy: (checked: boolean) => {
      useProxy.value = checked;
    },
    setUseLlm: (checked: boolean) => {
      useLlm.value = checked;
    },
    selectHistoryRun: (runId: number | null) => {
      selectedHistoryRunIdSignal.value = runId;
    },
    toggleProvider: (name: string) => {
      selectedProvidersOverride.value = toggleProviderName(selectedProviders, name);
    },
    triggerRun: () => triggerMutation.mutate(),
    triggerRejudge: () => rejudgeMutation.mutate(),
  };
}
