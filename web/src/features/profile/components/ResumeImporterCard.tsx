import { useSignal } from '@preact/signals-react';
import { FileUp, Sparkles, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';

/** Props for the AI resume upload and raw-text parser card. */
interface ResumeImporterCardProps {
  /** Whether the LLM parse request is currently running. */
  isParsing: boolean;
  /** Whether a parsed preview with suggested queries/skills is available to sync. */
  hasParsedPreview: boolean;
  /** Triggers LLM parsing with the selected file or pasted text. */
  onParse: (file: File | undefined, rawText: string | undefined) => void;
  /** Copies suggested queries and skills from the parsed preview into scraper config. */
  onSyncSuggestions: () => void;
}

/**
 * Dropzone and paste area for parsing any `.pdf`, `.md`, or `.txt` resume into a `MasterProfile`.
 */
export function ResumeImporterCard({
  isParsing,
  hasParsedPreview,
  onParse,
  onSyncSuggestions,
}: ResumeImporterCardProps) {
  const rawResumeText = useSignal('');
  const selectedFile = useSignal<File | null>(null);

  return (
    <Card className="border-emerald-200/80 bg-emerald-50/30 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-950">
          <Wand2 className="h-3.5 w-3.5 text-emerald-600" />
          Import & Parse Resume with AI
        </span>
        {hasParsedPreview && (
          <Button variant="outline" size="sm" onClick={onSyncSuggestions}>
            <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
            Sync Suggested Queries & Skills to Scraper
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-12">
        <div className="md:col-span-4 space-y-2">
          <label className="flex h-24 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-emerald-300 bg-white px-3 text-center hover:bg-emerald-50/40">
            <FileUp className="h-5 w-5 text-emerald-600" />
            <span className="mt-1 text-xs font-medium text-zinc-700">
              {selectedFile.value ? selectedFile.value.name : 'Upload .pdf, .md or .txt'}
            </span>
            <input
              type="file"
              accept=".pdf,.md,.txt"
              className="hidden"
              onChange={event => {
                selectedFile.value = event.target.files?.[0] ?? null;
              }}
            />
          </label>
        </div>
        <div className="md:col-span-8 space-y-2">
          <Textarea
            rows={4}
            value={rawResumeText.value}
            onChange={event => {
              rawResumeText.value = event.target.value;
            }}
            placeholder="Or paste raw resume Markdown / text here..."
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          variant="primary"
          size="sm"
          disabled={isParsing || (!selectedFile.value && !rawResumeText.value.trim())}
          onClick={() =>
            onParse(selectedFile.value ?? undefined, rawResumeText.value || undefined)
          }
        >
          <Sparkles className="h-3.5 w-3.5" />
          {isParsing ? 'Parsing...' : 'Parse Resume with LLM'}
        </Button>
      </div>
    </Card>
  );
}
