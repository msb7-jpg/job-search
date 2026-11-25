import { FormattedDescription } from '@/components/FormattedDescription';
import { Badge } from '@/components/ui/badge';
import type { JobDetail, TailoredDiff } from '@/types';

/** Props for the left-hand JD and keyword gap context pane. */
interface JobContextPaneProps {
  /** Full job detail record. */
  detail: JobDetail | undefined;
  /** Current tailored diff containing honest missing keywords. */
  diffDraft: TailoredDiff | null;
}

/**
 * Displays matched skills, honest missing keywords, and the full job description.
 */
export function JobContextPane({ detail, diffDraft }: JobContextPaneProps) {
  const matchedSkills = detail?.evaluation?.matched_skills ?? [];
  const missingKeywords = diffDraft?.missing_keywords_honest_note ?? [];

  return (
    <div className="flex min-h-0 flex-col gap-4 overflow-y-auto border-r border-zinc-200 bg-white p-5 lg:col-span-4">
      {matchedSkills.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
            Matched Skills
          </div>
          <div className="flex flex-wrap gap-1.5">
            {matchedSkills.map(skill => (
              <Badge key={skill} variant="mint">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {missingKeywords.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3 space-y-1.5">
          <div className="text-[11px] font-semibold text-amber-900">
            Honest Missing Keywords (not faked)
          </div>
          <div className="flex flex-wrap gap-1">
            {missingKeywords.map(keyword => (
              <Badge key={keyword} variant="amber">
                {keyword}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-1.5">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
          Job Description
        </div>
        <FormattedDescription text={detail?.description_md ?? ''} />
      </div>
    </div>
  );
}
