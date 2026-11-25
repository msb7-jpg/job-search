import { useSignal } from '@preact/signals-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { runKeys, runQueries } from '@/api/queries';
import { TOAST_VARIANT } from '@/lib/constants';
import { activeRunIdSignal, showToast, sseLogsSignal } from '@/state/signals';
import { useRunStream } from './useRunStream';

/**
 * Encapsulates scraper provider selection, run triggering, LLM rejudge, and live SSE streaming.
 */
export function useScraperActions() {
  const queryClient = useQueryClient();
  const overviewQuery = useQuery(runQueries.overview());
  const overview = overviewQuery.data;

  const selectedProvidersOverride = useSignal<string[] | null>(null);
  const useProxy = useSignal(true);
  const useLlm = useSignal(true);

  const selectedProviders =
    selectedProvidersOverride.value ?? overview?.available_providers ?? [];
  useRunStream(activeRunIdSignal.value);

  const startStream = (runId: string, label: string) => {
    sseLogsSignal.value = [`${label} ${runId}...`];
    activeRunIdSignal.value = runId;
    showToast(label);
    queryClient.invalidateQueries({ queryKey: runKeys.overview() });
  };

  const triggerMutation = useMutation({
    mutationFn: () =>
      apiFetch<{ run_id: string }>('/api/runs/trigger', {
        method: 'POST',
        body: JSON.stringify({
          providers: selectedProviders.length > 0 ? selectedProviders : null,
          use_proxy: useProxy.value,
          use_llm: useLlm.value,
        }),
      }),
    onSuccess: res => startStream(res.run_id, 'Started scrape run'),
    onError: err =>
      showToast(
        err instanceof Error ? err.message : 'Failed to start scrape run',
        TOAST_VARIANT.ERROR
      ),
  });

  const rejudgeMutation = useMutation({
    mutationFn: () => apiFetch<{ run_id: string }>('/api/runs/rejudge', { method: 'POST' }),
    onSuccess: res => startStream(res.run_id, 'Started LLM rejudge'),
    onError: err =>
      showToast(
        err instanceof Error ? err.message : 'Failed to start rejudge',
        TOAST_VARIANT.ERROR
      ),
  });

  const toggleProvider = (name: string) => {
    const next = selectedProviders.includes(name)
      ? selectedProviders.filter(prov => prov !== name)
      : [...selectedProviders, name];
    selectedProvidersOverride.value = next;
  };

  const isRunning = Boolean(overview?.is_running || activeRunIdSignal.value);

  return {
    overview,
    selectedProviders,
    useProxy: useProxy.value,
    useLlm: useLlm.value,
    isRunning,
    isTriggerPending: triggerMutation.isPending,
    setUseProxy: (checked: boolean) => {
      useProxy.value = checked;
    },
    setUseLlm: (checked: boolean) => {
      useLlm.value = checked;
    },
    toggleProvider,
    triggerRun: () => triggerMutation.mutate(),
    triggerRejudge: () => rejudgeMutation.mutate(),
  };
}
