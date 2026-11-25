import { studioJobIdSignal } from '@/state/signals';
import { JobContextPane } from './components/JobContextPane';
import { PdfPreviewPane } from './components/PdfPreviewPane';
import { ReviewStudioHeader } from './components/ReviewStudioHeader';
import { TailoredDiffEditor } from './components/TailoredDiffEditor';
import { useReviewStudio } from './hooks/useReviewStudio';

/**
 * Full-screen Review Studio modal orchestrating JD context, diff editing, and live 1-page PDF preview.
 */
export function ReviewStudioModal({ jobId }: { jobId: number }) {
  const studio = useReviewStudio(jobId);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#FAFAFA]">
      <ReviewStudioHeader
        title={studio.detail?.title ?? 'Loading...'}
        company={studio.detail?.company ?? ''}
        hasDiff={Boolean(studio.diffDraft)}
        includeCoverLetter={studio.includeCoverLetter}
        isGenerating={studio.isGenerating}
        isRerendering={studio.isRerendering}
        onToggleCoverLetter={studio.setIncludeCoverLetter}
        onGenerate={studio.handleGenerate}
        onRerender={studio.handleRerender}
        onMarkReady={studio.handleMarkReady}
        onClose={() => {
          studioJobIdSignal.value = null;
        }}
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-12">
        <JobContextPane detail={studio.detail} diffDraft={studio.diffDraft} />
        <TailoredDiffEditor
          diffDraft={studio.diffDraft}
          warnings={studio.warnings}
          pageCount={studio.pageCount}
          onChange={studio.setDiffDraft}
        />
        <PdfPreviewPane
          jobId={jobId}
          pdfVersion={studio.pdfVersion}
          hasPdf={Boolean(studio.diffDraft)}
        />
      </div>
    </div>
  );
}
