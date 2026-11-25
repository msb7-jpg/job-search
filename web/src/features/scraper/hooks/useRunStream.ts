import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { jobKeys, runKeys } from '@/api/queries';
import { SSE_EVENT_TYPE } from '@/lib/constants';
import { activeRunIdSignal, sseLogsSignal } from '@/state/signals';

/**
 * Subscribes to the FastAPI SSE log stream for an active background run.
 */
export function useRunStream(activeRunId: string | null) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!activeRunId) return;

    const eventSource = new EventSource(`/api/runs/${activeRunId}/stream`);
    eventSource.onmessage = event => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.type === SSE_EVENT_TYPE.LOG && parsed.line) {
          sseLogsSignal.value = [...sseLogsSignal.value.slice(-250), parsed.line];
        } else if (parsed.type === SSE_EVENT_TYPE.DONE) {
          eventSource.close();
          activeRunIdSignal.value = null;
          queryClient.invalidateQueries({ queryKey: runKeys.overview() });
          queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
        }
      } catch {
        // ignore parse errors
      }
    };
    eventSource.onerror = () => {
      eventSource.close();
    };
    return () => eventSource.close();
  }, [activeRunId, queryClient]);
}
