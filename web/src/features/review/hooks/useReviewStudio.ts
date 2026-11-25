import { usePatchTailor, useTailorJob, useUpdateJobStatus } from '@/api/mutations';
import { jobQueries } from '@/api/queries';
import { JOB_STATUS, TOAST_VARIANT } from '@/lib/constants';
import { showToast, studioJobIdSignal } from '@/state/signals';
import type { TailoredDiff, VerificationWarning } from '@/types';
import { useSignal } from '@preact/signals-react';
import { useQuery } from '@tanstack/react-query';

/**
 * Manages Review Studio state, AI resume generation, PDF re-rendering, and status transitions.
 */
export function useReviewStudio(jobId: number) {
  const detailQuery = useQuery(jobQueries.detail(jobId));
  const detail = detailQuery.data;

  const tailorMutation = useTailorJob();
  const patchMutation = usePatchTailor();
  const statusMutation = useUpdateJobStatus();

  const diffOverride = useSignal<TailoredDiff | null>(null);
  const warningsOverride = useSignal<VerificationWarning[] | null>(null);
  const pageCount = useSignal(1);
  const pdfVersion = useSignal(1);
  const includeCoverLetter = useSignal(false);

  const diffDraft = diffOverride.value ?? detail?.tailored_resume?.diff ?? null;
  const warnings =
    warningsOverride.value ?? detail?.tailored_resume?.verification_warnings ?? [];

  const handleGenerate = () => {
    tailorMutation.mutate(
      { jobId, includeCoverLetter: includeCoverLetter.value },
      {
        onSuccess: response => {
          diffOverride.value = response.diff;
          warningsOverride.value = response.verification_warnings;
          pageCount.value = response.page_count;
          pdfVersion.value += 1;
        },
        onError: error => {
          showToast(
            error instanceof Error ? error.message : 'Tailoring failed',
            TOAST_VARIANT.ERROR
          );
        },
      }
    );
  };

  const handleRerender = () => {
    if (!diffDraft) return;
    patchMutation.mutate(
      { jobId, diff: diffDraft, coverLetterMd: diffDraft.cover_letter_md },
      {
        onSuccess: res => {
          warningsOverride.value = res.verification_warnings;
          pageCount.value = res.page_count;
          pdfVersion.value += 1;
        },
      }
    );
  };

  const handleMarkReady = () => {
    statusMutation.mutate(
      { jobId, status: JOB_STATUS.READY_TO_APPLY },
      {
        onSuccess: () => {
          showToast('Marked Ready to Apply');
          studioJobIdSignal.value = null;
        },
      }
    );
  };

  return {
    detail,
    diffDraft,
    warnings,
    pageCount: pageCount.value,
    pdfVersion: pdfVersion.value,
    includeCoverLetter: includeCoverLetter.value,
    isGenerating: tailorMutation.isPending,
    isRerendering: patchMutation.isPending,
    setDiffDraft: (next: TailoredDiff | null) => {
      diffOverride.value = next;
    },
    setIncludeCoverLetter: (checked: boolean) => {
      includeCoverLetter.value = checked;
    },
    handleGenerate,
    handleRerender,
    handleMarkReady,
  };
}
