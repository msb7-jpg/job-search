import type { components } from '@/api/openapi';

/** OpenAPI schema dictionary generated from FastAPI. */
type Schemas = components['schemas'];

/** Application workflow status values. */
export type ApplicationStatus =
  | 'NEW'
  | 'SAVED'
  | 'TAILORING'
  | 'READY_TO_APPLY'
  | 'APPLIED'
  | 'INTERVIEWING'
  | 'OFFER'
  | 'REJECTED'
  | 'IGNORED';

/** Application tracking metadata attached to a job. */
export type JobApplication = Omit<Required<Schemas['ApplicationSchema']>, 'status'> & {
  /** Current workflow stage of the application. */
  status: ApplicationStatus;
};

/** Summary representation of a scraped job for list views. */
export type JobSummary = Omit<Required<Schemas['JobSummarySchema']>, 'application'> & {
  /** Optional user application state. */
  application?: JobApplication | null;
};

/** Skill category and its associated skill names. */
export type SkillGroup = Required<Schemas['SkillGroup']>;

/** Constrained LLM diff output for tailoring a resume to a job. */
export type TailoredDiff = Required<Schemas['TailoredDiff']>;

/** Deterministic anti-hallucination or page-overflow warning. */
export interface VerificationWarning {
  /** Identifier of the bullet (or `page_count`) that triggered the warning. */
  bullet_id: string;
  /** Machine-readable warning category. */
  warning_type: string;
  /** Human-readable explanation of the detected issue. */
  details: string;
  /** Original bullet text before tailoring. */
  original_text?: string;
  /** Tailored bullet text produced by the LLM or user. */
  tailored_text?: string;
}

/** Persisted tailored resume record returned inside job details. */
export type TailoredResumeSummary = Omit<
  Required<Schemas['TailoredResumeSummarySchema']>,
  'diff' | 'verification_warnings'
> & {
  /** Structured resume diff applied to the master profile. */
  diff: TailoredDiff;
  /** Anti-hallucination and page-count warnings. */
  verification_warnings: VerificationWarning[];
};

/** Full job detail payload including description, cross-provider siblings, and tailored resume. */
export type JobDetail = Omit<
  Required<Schemas['JobDetailSchema']>,
  'application' | 'tailored_resume'
> & {
  /** Optional user application state. */
  application?: JobApplication | null;
  /** Latest tailored resume generated for this job. */
  tailored_resume?: TailoredResumeSummary | null;
};

/** Paginated job list response. */
export type JobListResponse = Omit<Required<Schemas['JobListResponse']>, 'items'> & {
  /** Matching job summary items. */
  items: JobSummary[];
};

/** Overview of scrape runs, pending LLM count, and active providers. */
export type RunsOverviewResponse = Required<Schemas['RunsOverviewResponse']>;

/** Persisted log lines for a historical scrape run. */
export type ScrapeRunLogsResponse = Required<Schemas['ScrapeRunLogsResponse']>;

/** Dynamic search, scoring, and blacklist configuration editable in Settings. */
export type UserSearchConfig = Required<Schemas['UserSearchConfig']>;

/** Candidate contact and identity block from the Master Profile. */
export type ProfileIdentity = Required<Schemas['ProfileIdentity']>;

/** Single achievement bullet with a deterministic ID and skill tags. */
export type ExperienceBullet = Required<Schemas['ExperienceBullet']>;

/** Work experience entry containing role metadata and a bullet pool. */
export type ExperienceEntry = Omit<Required<Schemas['ExperienceEntry']>, 'bullets'> & {
  /** Pool of achievement bullets for this role. */
  bullets: ExperienceBullet[];
};

/** Education entry from the Master Profile. */
export type EducationEntry = Required<Schemas['EducationEntry']>;

/** Spoken language entry from the Master Profile. */
export type LanguageEntry = Required<Schemas['LanguageEntry']>;

/** Canonical candidate profile stored in `master_profile.json`. */
export type MasterProfile = Omit<
  Required<Schemas['MasterProfile']>,
  'identity' | 'experiences' | 'education' | 'skill_groups' | 'languages'
> & {
  /** Candidate contact and identity details. */
  identity: ProfileIdentity;
  /** Work experience entries. */
  experiences: ExperienceEntry[];
  /** Education entries. */
  education: EducationEntry[];
  /** Categorized skill groups. */
  skill_groups: SkillGroup[];
  /** Spoken languages. */
  languages: LanguageEntry[];
};

/** Result of parsing a raw resume via the LLM endpoint. */
export type ParsedResumeResult = Omit<Required<Schemas['ParsedResumeResult']>, 'profile'> & {
  /** Structured master profile extracted from the resume. */
  profile: MasterProfile;
};

/** Response returned after generating or re-rendering a tailored resume PDF. */
export type TailorResponse = Omit<
  Required<Schemas['TailorResponse']>,
  'diff' | 'verification_warnings'
> & {
  /** Structured resume diff. */
  diff: TailoredDiff;
  /** Anti-hallucination and page-count warnings. */
  verification_warnings: VerificationWarning[];
};
