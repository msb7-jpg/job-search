import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import type { UserSearchConfig } from '@/types';

/** Props for the search queries and skills map editor cards. */
interface QueriesSkillsCardProps {
  /** Current search configuration draft. */
  draft: UserSearchConfig;
  /** Raw JSON string for `skills_map`. */
  skillsText: string;
  /** Updates the search configuration draft. */
  onChangeDraft: (next: UserSearchConfig) => void;
  /** Updates the raw `skills_map` JSON string. */
  onChangeSkillsText: (text: string) => void;
}

/**
 * Editors for LinkedIn/job-board queries, ATS queries, and the skills normalization JSON map.
 */
export function QueriesSkillsCard({
  draft,
  skillsText,
  onChangeDraft,
  onChangeSkillsText,
}: QueriesSkillsCardProps) {
  const splitLines = (raw: string) =>
    raw
      .split('\n')
      .map(line => line.trim())
      .filter(Boolean);

  return (
    <>
      <Card className="p-4 space-y-2">
        <div className="text-xs font-semibold text-zinc-800">
          Job Board Queries (LinkedIn / etc., 1 per line)
        </div>
        <Textarea
          rows={6}
          className="font-mono text-[11px]"
          value={draft.queries_jobs.join('\n')}
          onChange={event =>
            onChangeDraft({ ...draft, queries_jobs: splitLines(event.target.value) })
          }
        />
      </Card>

      <Card className="p-4 space-y-2">
        <div className="text-xs font-semibold text-zinc-800">
          ATS Queries (Gupy / etc., 1 per line)
        </div>
        <Textarea
          rows={6}
          className="font-mono text-[11px]"
          value={draft.queries_ats.join('\n')}
          onChange={event =>
            onChangeDraft({ ...draft, queries_ats: splitLines(event.target.value) })
          }
        />
      </Card>

      <Card className="p-4 space-y-2 lg:col-span-2">
        <div className="text-xs font-semibold text-zinc-800">
          Skills Normalization Map (JSON)
        </div>
        <Textarea
          rows={8}
          className="font-mono text-[11px]"
          value={skillsText}
          onChange={event => onChangeSkillsText(event.target.value)}
        />
      </Card>
    </>
  );
}
