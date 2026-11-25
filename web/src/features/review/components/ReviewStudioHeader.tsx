import { CheckCircle2, RefreshCw, Sparkles, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

/** Props for the Review Studio modal top action bar. */
interface ReviewStudioHeaderProps {
  /** Target job title. */
  title: string;
  /** Target company name. */
  company: string;
  /** Whether a tailored diff has been generated yet. */
  hasDiff: boolean;
  /** Whether cover letter generation is enabled. */
  includeCoverLetter: boolean;
  /** Whether the initial LLM tailoring request is running. */
  isGenerating: boolean;
  /** Whether the PDF re-render request is running. */
  isRerendering: boolean;
  /** Toggles cover letter generation. */
  onToggleCoverLetter: (checked: boolean) => void;
  /** Triggers LLM tailoring and PDF rendering. */
  onGenerate: () => void;
  /** Saves manual edits and re-renders the PDF. */
  onRerender: () => void;
  /** Transitions the job status to `READY_TO_APPLY` and closes the modal. */
  onMarkReady: () => void;
  /** Closes the Review Studio modal. */
  onClose: () => void;
}

/**
 * Sticky header bar with tailoring, PDF re-render, and status actions for Review Studio.
 */
export function ReviewStudioHeader({
  title,
  company,
  hasDiff,
  includeCoverLetter,
  isGenerating,
  isRerendering,
  onToggleCoverLetter,
  onGenerate,
  onRerender,
  onMarkReady,
  onClose,
}: ReviewStudioHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-5 py-3">
      <div className="flex items-center gap-3">
        <Badge variant="mint">Review Studio</Badge>
        <div>
          <div className="text-sm font-semibold text-zinc-900">{title}</div>
          <div className="text-xs text-zinc-500">{company}</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <label className="mr-2 inline-flex items-center gap-1.5 text-xs text-zinc-600 cursor-pointer">
          <input
            type="checkbox"
            checked={includeCoverLetter}
            onChange={event => onToggleCoverLetter(event.target.checked)}
            className="accent-emerald-600"
          />
          Cover Letter
        </label>

        <Button variant="primary" size="sm" onClick={onGenerate} disabled={isGenerating}>
          <Sparkles className="h-3.5 w-3.5" />
          {isGenerating ? 'Generating...' : 'Generate Tailored Resume'}
        </Button>

        {hasDiff && (
          <>
            <Button variant="outline" size="sm" onClick={onRerender} disabled={isRerendering}>
              <RefreshCw className="h-3.5 w-3.5" />
              Re-render PDF
            </Button>
            <Button variant="default" size="sm" onClick={onMarkReady}>
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Ready to Apply
            </Button>
          </>
        )}

        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
