import { useBlacklistCompany, useUpdateJobStatus } from '@/api/mutations';
import { jobQueries } from '@/api/queries';
import { DataTable } from '@/components/DataTable';
import { Input } from '@/components/ui/input';
import { JOB_STATUS, LLM_STATUS } from '@/lib/constants';
import { showToast } from '@/state/signals';
import { useSignal } from '@preact/signals-react';
import { useQuery } from '@tanstack/react-query';
import { buildRejectionColumns } from './columns';

/**
 * Page orchestrator for inspecting Layer 1 / Layer 2 rejections and rescuing false negatives.
 */
export function RejectionAuditPage() {
  const layerFilter = useSignal('');
  const query = useQuery(
    jobQueries.list({
      llm_status: `${LLM_STATUS.REJECTED},${LLM_STATUS.SKIPPED}`,
      discard_layer: layerFilter.value || undefined,
      limit: 300,
    })
  );

  const jobs = query.data?.items ?? [];
  const rescueMutation = useUpdateJobStatus();
  const blacklistMutation = useBlacklistCompany();

  const columns = buildRejectionColumns(
    jobId =>
      rescueMutation.mutate(
        { jobId, status: JOB_STATUS.SAVED },
        { onSuccess: () => showToast('Job rescued to Saved') }
      ),
    companyName => blacklistMutation.mutate({ companyName })
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">Rejection Audit Log</h2>
          <p className="text-xs text-zinc-500">
            Inspect Layer 1 heuristics and Layer 2 LLM rejections. Rescue false negatives in 1 click.
          </p>
        </div>
        <Input
          value={layerFilter.value}
          onChange={event => {
            layerFilter.value = event.target.value;
          }}
          placeholder="Filter by layer (e.g. Camada 1, LLM)..."
          className="w-64"
        />
      </div>

      <DataTable
        columns={columns}
        data={jobs}
        searchColumn="title"
        searchPlaceholder="Search rejected roles or companies..."
      />
    </div>
  );
}
