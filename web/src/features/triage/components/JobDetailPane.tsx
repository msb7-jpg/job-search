import {
  Ban,
  Bookmark,
  ExternalLink,
  FileText,
  Layers,
  MapPin,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { FormattedDescription } from '@/components/FormattedDescription';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import type { JobDetail } from '@/types';

/** Props for the right-hand Triage Inbox job detail pane. */
interface JobDetailPaneProps {
  /** Full job detail record, or `undefined` when nothing is selected. */
  detail: JobDetail | undefined;
  /** Opens the Review Studio modal for the given job ID. */
  onTailor: (jobId: number) => void;
  /** Marks the selected job as `SAVED`. */
  onSave: () => void;
  /** Marks the selected job as `IGNORED`. */
  onIgnore: () => void;
  /** Adds the selected job's company to the dynamic blacklist. */
  onBlacklist: (companyName: string) => void;
}

/** Formats a deduplicated sibling link label using location when provider matches the active job. */
function formatSiblingLabel(sibling: NonNullable<JobDetail['siblings']>[number], baseProvider: string): string {
  const loc = sibling.location?.trim();
  if (sibling.provider === baseProvider) {
    return loc || sibling.provider;
  }
  return loc ? `${sibling.provider} (${loc})` : sibling.provider;
}

/** Deduplicates sibling postings by `(provider, location)` excluding the current job. */
function getUniqueSiblings(detail: JobDetail) {
  const seen = new Set<string>([`${detail.provider}::${detail.location?.trim() || ''}`]);
  return detail.siblings.filter(sibling => {
    const key = `${sibling.provider}::${sibling.location?.trim() || ''}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Displays the selected job's metadata, cross-provider siblings, AI Judge assessment, and description.
 */
export function JobDetailPane({
  detail,
  onTailor,
  onSave,
  onIgnore,
  onBlacklist,
}: JobDetailPaneProps) {
  if (!detail) {
    return (
      <Card className="flex min-h-0 flex-col overflow-hidden lg:col-span-7">
        <div className="flex flex-1 items-center justify-center text-xs text-zinc-400">
          Select a job to inspect details
        </div>
      </Card>
    );
  }

  return (
    <Card className="flex min-h-0 flex-col overflow-hidden lg:col-span-7">
      <div className="border-b border-zinc-100 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{detail.provider}</Badge>
              <Badge variant="mint">{detail.work_model}</Badge>
              <Badge variant="neutral">{detail.seniority}</Badge>
            </div>
            <h2 className="mt-2 text-base font-semibold tracking-tight text-zinc-950">
              {detail.title}
            </h2>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <span className="font-medium text-zinc-800">{detail.company}</span>
              <span>•</span>
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {detail.location}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <Button variant="primary" size="sm" onClick={() => onTailor(detail.id)} aria-keyshortcuts="T">
              <FileText className="h-3.5 w-3.5" />
              Tailor
            </Button>
            <Button variant="outline" size="sm" onClick={onSave} aria-keyshortcuts="S">
              <Bookmark className="h-3.5 w-3.5" />
              Save
            </Button>
            <Button variant="ghost" size="sm" onClick={onIgnore} aria-keyshortcuts="X">
              <XCircle className="h-3.5 w-3.5" />
              Ignore
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => onBlacklist(detail.company)}
              title="Add company to blacklist"
            >
              <Ban className="h-3.5 w-3.5" />
              Blacklist
            </Button>
            <a
              href={detail.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-7 items-center gap-1 rounded-md border border-zinc-200 bg-white px-2.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Open
            </a>
          </div>
        </div>

        {(() => {
          const uniqueSiblings = getUniqueSiblings(detail);
          if (uniqueSiblings.length === 0) return null;
          const allSameProvider = uniqueSiblings.every(
            sibling => sibling.provider === detail.provider
          );
          return (
            <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-zinc-200/80 bg-zinc-50 px-3 py-1.5 text-[11px] text-zinc-600">
              <Layers className="h-3.5 w-3.5 text-emerald-600" />
              <span>{allSameProvider ? 'Other locations:' : 'Also found on:'}</span>
              {uniqueSiblings.map(sibling => (
                <a
                  key={sibling.id}
                  href={sibling.url}
                  target="_blank"
                  rel="noreferrer"
                  title={`${sibling.provider}${sibling.location ? ` — ${sibling.location}` : ''}`}
                  className="font-medium text-emerald-700 underline-offset-2 hover:underline"
                >
                  {formatSiblingLabel(sibling, detail.provider)}
                </a>
              ))}
            </div>
          );
        })()}
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {detail.evaluation && (
          <div className="rounded-xl border border-emerald-200/80 bg-emerald-50/45 p-3.5">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-900">
                <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                AI Judge Assessment
              </span>
              <div className="flex items-center gap-2 font-mono text-[11px]">
                <span className="text-zinc-600">L1: {detail.evaluation.layer1_score}%</span>
                <Badge variant="mint">LLM: {detail.evaluation.llm_score}%</Badge>
              </div>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-zinc-700">
              {detail.evaluation.llm_reasoning}
            </p>
            {detail.evaluation.matched_skills.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {detail.evaluation.matched_skills.map(skill => (
                  <Badge key={skill} variant="mint">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Job Description
          </h3>
          <FormattedDescription text={detail.description_md} />
        </div>
      </div>
    </Card>
  );
}
