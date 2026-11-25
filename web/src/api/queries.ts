import { queryOptions } from '@tanstack/react-query';
import { apiFetch } from '@/api/client';
import type {
  JobDetail,
  JobListResponse,
  MasterProfile,
  RunsOverviewResponse,
  UserSearchConfig,
} from '@/types';

/** Filter parameters supported by `GET /api/jobs`. */
export interface JobFilters {
  /** Comma-separated application statuses. */
  status?: string;
  /** Comma-separated LLM evaluation statuses. */
  llm_status?: string;
  /** Exact provider name filter. */
  provider?: string;
  /** Minimum evaluation score threshold. */
  min_score?: number;
  /** Substring filter on `discard_layer`. */
  discard_layer?: string;
  /** Full-text search across title, company, location, and description. */
  search?: string;
  /** Maximum number of rows to return. */
  limit?: number;
  /** Pagination offset. */
  offset?: number;
}

/** Hierarchical TanStack Query key factory for job queries. */
export const jobKeys = {
  all: ['jobs'] as const,
  lists: () => [...jobKeys.all, 'list'] as const,
  list: (filters: JobFilters) => [...jobKeys.lists(), filters] as const,
  details: () => [...jobKeys.all, 'detail'] as const,
  detail: (id: number) => [...jobKeys.details(), id] as const,
};

/** Hierarchical TanStack Query key factory for scrape run queries. */
export const runKeys = {
  all: ['runs'] as const,
  overview: () => [...runKeys.all, 'overview'] as const,
};

/** TanStack Query key factory for dynamic search config. */
export const configKeys = {
  all: ['config'] as const,
};

/** TanStack Query key factory for the candidate Master Profile. */
export const profileKeys = {
  all: ['profile'] as const,
};

/**
 * Serializes defined job filter parameters into a `/api/jobs` URL string.
 */
function buildJobsQueryString(filters: JobFilters): string {
  const params = new URLSearchParams();
  for (const [filterKey, filterVal] of Object.entries(filters)) {
    if (filterVal !== undefined && filterVal !== '') {
      params.set(filterKey, String(filterVal));
    }
  }
  const queryStr = params.toString();
  return queryStr ? `/api/jobs?${queryStr}` : '/api/jobs';
}

/** Co-located `queryOptions` definitions for job list and detail endpoints. */
export const jobQueries = {
  list: (filters: JobFilters) =>
    queryOptions({
      queryKey: jobKeys.list(filters),
      queryFn: () => apiFetch<JobListResponse>(buildJobsQueryString(filters)),
      staleTime: 15_000,
    }),
  detail: (id: number) =>
    queryOptions({
      queryKey: jobKeys.detail(id),
      queryFn: () => apiFetch<JobDetail>(`/api/jobs/${id}`),
      staleTime: 30_000,
      enabled: id > 0,
    }),
};

/** Co-located `queryOptions` for scraper run history and status. */
export const runQueries = {
  overview: () =>
    queryOptions({
      queryKey: runKeys.overview(),
      queryFn: () => apiFetch<RunsOverviewResponse>('/api/runs'),
      refetchInterval: 5_000,
    }),
};

/** Co-located `queryOptions` for dynamic search & blacklist configuration. */
export const configQueries = {
  get: () =>
    queryOptions({
      queryKey: configKeys.all,
      queryFn: () => apiFetch<UserSearchConfig>('/api/config'),
      staleTime: 60_000,
    }),
};

/** Co-located `queryOptions` for the candidate Master Profile. */
export const profileQueries = {
  get: () =>
    queryOptions({
      queryKey: profileKeys.all,
      queryFn: () => apiFetch<MasterProfile>('/api/profile'),
      staleTime: 60_000,
    }),
};
