/** Props for the right-hand inline PDF preview pane. */
interface PdfPreviewPaneProps {
  /** Target job ID whose tailored PDF is served at `/api/jobs/{id}/resume.pdf`. */
  jobId: number;
  /** Cache-busting version counter incremented on each render. */
  pdfVersion: number;
  /** Whether a tailored PDF has been generated. */
  hasPdf: boolean;
}

/**
 * Inline `<iframe>` preview of the generated 1-page ATS resume PDF.
 */
export function PdfPreviewPane({ jobId, pdfVersion, hasPdf }: PdfPreviewPaneProps) {
  return (
    <div className="flex min-h-0 flex-col border-l border-zinc-200 bg-zinc-100 p-4 lg:col-span-4">
      {hasPdf ? (
        <iframe
          key={pdfVersion}
          title="Tailored Resume PDF"
          src={`/api/jobs/${jobId}/resume.pdf?v=${pdfVersion}`}
          className="h-full w-full rounded-lg border border-zinc-200 bg-white shadow-xs"
        />
      ) : (
        <div className="flex flex-1 items-center justify-center text-xs text-zinc-400">
          PDF preview will appear here
        </div>
      )}
    </div>
  );
}
