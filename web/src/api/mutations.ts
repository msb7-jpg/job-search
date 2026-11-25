import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import { configKeys, jobKeys, profileKeys } from '@/api/queries';
import { TOAST_VARIANT } from '@/lib/constants';
import { showToast } from '@/state/signals';
import type {
  ApplicationStatus,
  MasterProfile,
  ParsedResumeResult,
  TailoredDiff,
  TailorResponse,
  UserSearchConfig,
} from '@/types';

/**
 * Updates a job's application workflow status and optional notes.
 */
export function useUpdateJobStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, status, notes,}: {
      jobId: number;
      status: ApplicationStatus;
      notes?: string;
    }) => apiFetch(`/api/jobs/${jobId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, notes }),
      }),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: jobKeys.detail(variables.jobId) }),
        queryClient.invalidateQueries({ queryKey: jobKeys.lists() }),
      ]);
    },
  });
}

/**
 * Adds a company to the dynamic blacklist and optionally ignores existing matching jobs.
 */
export function useBlacklistCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyName, ignoreExisting = true }: {
      companyName: string;
      ignoreExisting?: boolean;
    }) =>
      apiFetch<{ blacklisted_companies: string[]; ignored_jobs_count: number }>(
        '/api/config/blacklist',
        {
          method: 'POST',
          body: JSON.stringify({
            company_name: companyName,
            ignore_existing: ignoreExisting,
          }),
        }
      ),
    onSuccess: async (res, vars) => {
      showToast(`Blacklisted "${vars.companyName}" (${res.ignored_jobs_count} jobs ignored)`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: configKeys.all }),
        queryClient.invalidateQueries({ queryKey: jobKeys.lists() }),
      ]);
    },
  });
}

/**
 * Persists updates to the dynamic search, scoring, and blacklist configuration.
 */
export function useUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: UserSearchConfig) =>
      apiFetch<UserSearchConfig>('/api/config', {
        method: 'PUT',
        body: JSON.stringify(config),
      }),
    onSuccess: async () => {
      showToast('Search & filter settings saved');
      await queryClient.invalidateQueries({ queryKey: configKeys.all });
    },
    onError: err => {
      showToast(err instanceof Error ? err.message : 'Failed to save settings', TOAST_VARIANT.ERROR);
    },
  });
}

/**
 * Persists updates to the candidate Master Profile and Q&A Fact Vault.
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (profile: MasterProfile) =>
      apiFetch<MasterProfile>('/api/profile', {
        method: 'PUT',
        body: JSON.stringify(profile),
      }),
    onSuccess: async () => {
      showToast('Master profile saved');
      await queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
    onError: err => {
      showToast(err instanceof Error ? err.message : 'Failed to save profile', TOAST_VARIANT.ERROR);
    },
  });
}

/**
 * Sends an uploaded resume file or raw text to the LLM parser endpoint.
 */
export function useParseResume() {
  return useMutation({
    mutationFn: ({ file, rawText }: { file?: File; rawText?: string }) => {
      const form = new FormData();
      if (file) form.append('file', file);
      if (rawText) form.append('raw_text', rawText);
      return apiFetch<ParsedResumeResult>('/api/profile/parse', {
        method: 'POST',
        body: form,
      });
    },
  });
}

/**
 * Generates a constrained `TailoredDiff` and 1-page ATS PDF for a job.
 */
export function useTailorJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      jobId,
      includeCoverLetter = false,
    }: {
      jobId: number;
      includeCoverLetter?: boolean;
    }) =>
      apiFetch<TailorResponse>(`/api/jobs/${jobId}/tailor`, {
        method: 'POST',
        body: JSON.stringify({ include_cover_letter: includeCoverLetter }),
      }),
    onSuccess: async (_data, vars) => {
      showToast('Resume tailored & 1-page PDF generated');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: jobKeys.detail(vars.jobId) }),
        queryClient.invalidateQueries({ queryKey: jobKeys.lists() }),
      ]);
    },
  });
}

/**
 * Saves manual Review Studio edits to the tailored diff and re-renders the PDF.
 */
export function usePatchTailor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      jobId,
      diff,
      coverLetterMd,
    }: {
      jobId: number;
      diff: TailoredDiff;
      coverLetterMd: string;
    }) =>
      apiFetch<TailorResponse>(`/api/jobs/${jobId}/tailor`, {
        method: 'PATCH',
        body: JSON.stringify({ diff, cover_letter_md: coverLetterMd }),
      }),
    onSuccess: async (_data, vars) => {
      showToast('PDF re-rendered');
      await queryClient.invalidateQueries({ queryKey: jobKeys.detail(vars.jobId) });
    },
  });
}
