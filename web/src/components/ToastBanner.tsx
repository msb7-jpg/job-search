import { AlertCircle, CheckCircle2, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ToastPayload } from '@/state/signals';

/** Props for the global top-right toast banner. */
interface ToastBannerProps {
  /** Active toast payload, or `null` when hidden. */
  toast: ToastPayload | null;
  /** Dismisses the active toast notification. */
  onDismiss: () => void;
}

/**
 * High-contrast top-right toast notification supporting success, error, and info variants.
 */
export function ToastBanner({ toast, onDismiss }: ToastBannerProps) {
  if (!toast) return null;

  const isError = toast.variant === 'error';

  return (
    <div
      className={cn(
        'fixed top-16 right-5 z-50 flex max-w-md items-start gap-2.5 rounded-xl border px-4 py-3 text-xs font-medium shadow-lg',
        isError
          ? 'border-red-300 bg-red-50 text-red-950'
          : 'border-emerald-300 bg-emerald-50 text-emerald-950'
      )}
    >
      {isError ? (
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
      ) : (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
      )}
      <span className="leading-relaxed">{toast.message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="ml-1 rounded p-0.5 opacity-60 hover:opacity-100 cursor-pointer"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
