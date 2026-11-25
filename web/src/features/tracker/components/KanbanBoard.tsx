import {
  DndContext,
  type DragEndEvent,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ExternalLink, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ApplicationStatus, JobSummary } from '@/types';
import { KANBAN_COLUMNS } from '../constants';

/**
 * Draggable application card rendered inside a Kanban column.
 */
function DraggableJobCard({
  job,
  onTailor,
  onSelectNotes,
}: {
  job: JobSummary;
  onTailor: (jobId: number) => void;
  onSelectNotes: (job: JobSummary) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: job.id });

  const style = { transform: CSS.Transform.toString(transform), transition };
  const score = job.evaluation?.llm_score || job.evaluation?.layer1_score || 0;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        'rounded-lg border border-zinc-200 bg-white p-3 shadow-xs transition-shadow hover:border-emerald-300 cursor-grab active:cursor-grabbing',
        isDragging && 'opacity-50 shadow-md'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-xs font-semibold text-zinc-900">{job.title}</div>
          <div className="truncate text-[11px] text-zinc-500">{job.company}</div>
        </div>
        <Badge variant="mint" className="font-mono shrink-0">
          {score}%
        </Badge>
      </div>

      {job.application?.notes && (
        <p className="mt-2 line-clamp-2 rounded bg-zinc-50 px-2 py-1 text-[11px] text-zinc-600">
          {job.application.notes}
        </p>
      )}

      <div className="mt-2.5 flex items-center justify-between gap-1 pt-1 border-t border-zinc-100">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onPointerDown={event => event.stopPropagation()}
            onClick={() => onTailor(job.id)}
            className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium text-emerald-700 hover:bg-emerald-50 cursor-pointer"
          >
            <FileText className="h-3 w-3" />
            Tailor
          </button>
          <button
            type="button"
            onPointerDown={event => event.stopPropagation()}
            onClick={() => onSelectNotes(job)}
            className="rounded px-1.5 py-0.5 text-[11px] text-zinc-500 hover:bg-zinc-100 cursor-pointer"
          >
            Notes
          </button>
        </div>
        <a
          href={job.url}
          target="_blank"
          rel="noreferrer"
          onPointerDown={event => event.stopPropagation()}
          className="text-zinc-400 hover:text-zinc-700"
        >
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}

/**
 * Droppable Kanban column representing a single application workflow stage.
 */
function KanbanColumn({
  id,
  label,
  jobs,
  onTailor,
  onSelectNotes,
}: {
  id: ApplicationStatus;
  label: string;
  jobs: JobSummary[];
  onTailor: (jobId: number) => void;
  onSelectNotes: (job: JobSummary) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex min-h-[420px] flex-col rounded-xl border border-zinc-200/80 bg-zinc-50/60 p-2.5 transition-colors',
        isOver && 'border-emerald-400 bg-emerald-50/40'
      )}
    >
      <div className="mb-2.5 flex items-center justify-between px-1">
        <span className="text-xs font-semibold text-zinc-700">{label}</span>
        <Badge variant="neutral" className="font-mono">
          {jobs.length}
        </Badge>
      </div>
      <div className="flex flex-1 flex-col gap-2">
        {jobs.map(job => (
          <DraggableJobCard
            key={job.id}
            job={job}
            onTailor={onTailor}
            onSelectNotes={onSelectNotes}
          />
        ))}
      </div>
    </div>
  );
}

/** Props for the `@dnd-kit` Application Tracker Kanban board. */
interface KanbanBoardProps {
  /** Tracked application jobs across all active stages. */
  jobs: JobSummary[];
  /** Moves a job card to a new application status. */
  onMoveStatus: (jobId: number, status: ApplicationStatus) => void;
  /** Opens the Review Studio modal for a job. */
  onTailor: (jobId: number) => void;
  /** Opens the notes editor modal for a job. */
  onSelectNotes: (job: JobSummary) => void;
}

/**
 * Drag-and-drop Kanban board powered by `@dnd-kit/core`.
 */
export function KanbanBoard({
  jobs,
  onMoveStatus,
  onTailor,
  onSelectNotes,
}: KanbanBoardProps) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;
    const jobId = Number(active.id);
    const targetStatus = String(over.id) as ApplicationStatus;
    const job = jobs.find(item => item.id === jobId);
    if (!job || job.application?.status === targetStatus) return;
    onMoveStatus(jobId, targetStatus);
  };

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {KANBAN_COLUMNS.map(col => (
          <KanbanColumn
            key={col.id}
            id={col.id}
            label={col.label}
            jobs={jobs.filter(job => job.application?.status === col.id)}
            onTailor={onTailor}
            onSelectNotes={onSelectNotes}
          />
        ))}
      </div>
    </DndContext>
  );
}
