import { useSignal } from '@preact/signals-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import type { JobSummary } from '@/types';

/** Props for the application notes editor modal. */
interface NotesModalProps {
  /** Job whose application notes are being edited. */
  job: JobSummary;
  /** Closes the modal without saving. */
  onClose: () => void;
  /** Persists the updated notes string. */
  onSave: (notes: string) => void;
}

/**
 * Shadcn Dialog modal for editing recruiter/interview notes on a tracked application.
 */
export function NotesModal({ job, onClose, onSave }: NotesModalProps) {
  const notesDraft = useSignal(job.application?.notes ?? '');

  return (
    <Dialog open onOpenChange={isOpen => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xs font-semibold">
            Notes — {job.title} ({job.company})
          </DialogTitle>
        </DialogHeader>
        <Textarea
          rows={4}
          value={notesDraft.value}
          onChange={event => {
            notesDraft.value = event.target.value;
          }}
          placeholder="Recruiter contact, salary range, next interview..."
        />
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={() => onSave(notesDraft.value)}>
            Save Notes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
