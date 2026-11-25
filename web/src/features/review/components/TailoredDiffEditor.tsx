import { AlertTriangle, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { WARNING_TYPE } from '@/lib/constants';
import type { TailoredDiff, VerificationWarning } from '@/types';

/** Props for the middle editable tailored diff and verification warning pane. */
interface TailoredDiffEditorProps {
  /** Current tailored diff, or `null` before generation. */
  diffDraft: TailoredDiff | null;
  /** Anti-hallucination and page-overflow warnings. */
  warnings: VerificationWarning[];
  /** Rendered PDF page count. */
  pageCount: number;
  /** Updates the tailored diff draft. */
  onChange: (next: TailoredDiff) => void;
}

/**
 * Editable form for headline, summary, selected bullets, and cover letter with anti-hallucination badges.
 */
export function TailoredDiffEditor({
  diffDraft,
  warnings,
  pageCount,
  onChange,
}: TailoredDiffEditorProps) {
  if (!diffDraft) {
    return (
      <div className="flex min-h-0 flex-col gap-4 overflow-y-auto p-5 lg:col-span-4">
        <div className="flex flex-1 flex-col items-center justify-center gap-2 text-center text-xs text-zinc-400">
          <FileText className="h-8 w-8 text-zinc-300" />
          <p>Click "Generate Tailored Resume" to create a constrained diff and 1-page PDF.</p>
        </div>
      </div>
    );
  }

  const overflowWarning = warnings.find(
    warn => warn.warning_type === WARNING_TYPE.OVERFLOW_PAGES
  );
  const bulletWarnings = warnings.filter(
    warn => warn.warning_type !== WARNING_TYPE.OVERFLOW_PAGES
  );

  return (
    <div className="flex min-h-0 flex-col gap-4 overflow-y-auto p-5 lg:col-span-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-800">Tailored Content</span>
        {overflowWarning ? (
          <Badge variant="danger">
            <AlertTriangle className="h-3 w-3" />
            {overflowWarning.details}
          </Badge>
        ) : (
          <Badge variant="mint">Pages: {pageCount} (ATS-Safe)</Badge>
        )}
      </div>

      {bulletWarnings.length > 0 && (
        <div className="space-y-2 rounded-lg border border-amber-300 bg-amber-50 p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900">
            <AlertTriangle className="h-3.5 w-3.5" />
            Anti-Hallucination Check ({bulletWarnings.length})
          </div>
          {bulletWarnings.map(warn => (
            <div key={`${warn.bullet_id}-${warn.warning_type}`} className="text-[11px] text-amber-800">
              <span className="font-mono font-semibold">{warn.bullet_id}:</span> {warn.details}
            </div>
          ))}
        </div>
      )}

      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-zinc-500">Headline</label>
        <Input
          value={diffDraft.headline}
          onChange={event => onChange({ ...diffDraft, headline: event.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-zinc-500">Tailored Summary</label>
        <Textarea
          rows={4}
          value={diffDraft.tailored_summary}
          onChange={event => onChange({ ...diffDraft, tailored_summary: event.target.value })}
        />
      </div>

      <div className="space-y-2">
        <label className="text-[11px] font-medium text-zinc-500">
          Selected Bullets ({Object.keys(diffDraft.bullet_overrides).length})
        </label>
        {Object.entries(diffDraft.bullet_overrides).map(([bulletId, bulletText]) => {
          const hasWarn = bulletWarnings.some(warn => warn.bullet_id === bulletId);
          return (
            <div key={bulletId} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] text-zinc-500">{bulletId}</span>
                {hasWarn && <Badge variant="amber">Check metric</Badge>}
              </div>
              <Textarea
                rows={2}
                className={hasWarn ? 'border-amber-400 bg-amber-50/30' : ''}
                value={bulletText}
                onChange={event =>
                  onChange({
                    ...diffDraft,
                    bullet_overrides: {
                      ...diffDraft.bullet_overrides,
                      [bulletId]: event.target.value,
                    },
                  })
                }
              />
            </div>
          );
        })}
      </div>

      {diffDraft.cover_letter_md && (
        <div className="space-y-1.5">
          <label className="text-[11px] font-medium text-zinc-500">Cover Letter</label>
          <Textarea
            rows={6}
            value={diffDraft.cover_letter_md}
            onChange={event => onChange({ ...diffDraft, cover_letter_md: event.target.value })}
          />
        </div>
      )}
    </div>
  );
}
