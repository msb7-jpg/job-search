import { useBlacklistCompany, useUpdateJobStatus } from '@/api/mutations';
import { jobQueries } from '@/api/queries';
import { JOB_STATUS, JobStatus, LLM_STATUS } from '@/lib/constants';
import { selectedJobIdSignal, showToast, studioJobIdSignal } from '@/state/signals';
import type { JobSummary } from '@/types';
import { useComputed, useSignal } from '@preact/signals-react';
import { useDebounce } from '@reactuses/core';
import { useQuery } from '@tanstack/react-query';
import { InboxList } from './components/InboxList';
import { JobDetailPane } from './components/JobDetailPane';
import { TriageToolbar } from './components/TriageToolbar';
import { useTriageKeyboard } from './hooks/useTriageKeyboard';

/**
 * Page orchestrator for the Triage Inbox split-pane view.
 */
export function TriageInboxPage() {
  const searchInput = useSignal('');
  const providerFilter = useSignal('');
  const jobsSignal = useSignal<JobSummary[]>([]);
  const debouncedSearch = useDebounce(searchInput.value, 250);

  const listQuery = useQuery(
    jobQueries.list({
      status: JOB_STATUS.NEW,
      llm_status: LLM_STATUS.APPROVED,
      provider: providerFilter.value || undefined,
      search: debouncedSearch || undefined,
      limit: 150,
    })
  );

  jobsSignal.value = listQuery.data?.items ?? [];

  const activeSelectedId = useComputed(() => {
    const currentJobs = jobsSignal.value;
    if (currentJobs.length === 0) return null;
    const isValid = currentJobs.some(job => job.id === selectedJobIdSignal.value);
    return isValid ? selectedJobIdSignal.value : (currentJobs[0]?.id ?? null);
  });

  const detailQuery = useQuery(jobQueries.detail(activeSelectedId.value ?? 0));
  const statusMutation = useUpdateJobStatus();
  const blacklistMutation = useBlacklistCompany();

  const moveSelection = (delta: number) => {
    const currentJobs = jobsSignal.value;
    if (!currentJobs.length) return;
    const currentIdx = currentJobs.findIndex(job => job.id === activeSelectedId.value);
    const baseIdx = currentIdx === -1 ? 0 : currentIdx;
    const nextIdx = Math.max(0, Math.min(currentJobs.length - 1, baseIdx + delta));
    selectedJobIdSignal.value = currentJobs[nextIdx]?.id ?? null;
  };

  const handleStatusAction = (status: Extract<JobStatus, 'SAVED' | 'IGNORED'>) => {
    const targetId = activeSelectedId.value;
    if (!targetId) return;
    const currentJobs = jobsSignal.value;
    const currentIdx = currentJobs.findIndex(job => job.id === targetId);
    const nextJob = currentJobs[currentIdx + 1] ?? currentJobs[currentIdx - 1] ?? null;
    statusMutation.mutate(
      { jobId: targetId, status },
      {
        onSuccess: () => {
          showToast(status === JOB_STATUS.SAVED ? 'Saved to Tracker' : 'Job ignored');
          selectedJobIdSignal.value = nextJob?.id ?? null;
        },
      }
    );
  };

  useTriageKeyboard({
    selectedJobId: activeSelectedId.value,
    selectedJobUrl: detailQuery.data?.url,
    onMoveSelection: moveSelection,
    onStatusAction: handleStatusAction,
  });

  const providers = useComputed(() =>
    Array.from(new Set(jobsSignal.value.map(job => job.provider))).sort()
  );

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col gap-3">
      <TriageToolbar
        searchInput={searchInput.value}
        providerFilter={providerFilter.value}
        providers={providers.value}
        onSearchChange={val => {
          searchInput.value = val;
        }}
        onProviderChange={val => {
          providerFilter.value = val;
        }}
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-12">
        <InboxList
          jobs={jobsSignal.value}
          isLoading={listQuery.isLoading}
          selectedId={activeSelectedId.value}
          onSelectJob={jobId => {
            selectedJobIdSignal.value = jobId;
          }}
        />
        <JobDetailPane
          detail={detailQuery.data}
          onTailor={jobId => {
            studioJobIdSignal.value = jobId;
          }}
          onSave={() => handleStatusAction(JOB_STATUS.SAVED)}
          onIgnore={() => handleStatusAction(JOB_STATUS.IGNORED)}
          onBlacklist={companyName => blacklistMutation.mutate({ companyName })}
        />
      </div>
    </div>
  );
}
