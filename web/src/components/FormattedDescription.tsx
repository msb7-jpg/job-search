import type { ReactNode } from 'react';

/** Props for the lightweight Markdown job description renderer. */
interface FormattedDescriptionProps {
  /** Markdown or plain-text job description content. */
  text: string;
}

/**
 * Renders inline `**bold**` spans inside a description line.
 */
function renderInlineBold(lineText: string): ReactNode[] {
  const parts = lineText.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    const isBold = part.startsWith('**') && part.endsWith('**') && part.length > 4;
    if (isBold) {
      return (
        <strong key={idx} className="font-semibold text-zinc-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

/**
 * Renders scraped job descriptions with headings, bullet lists, bold spans, and paragraph spacing.
 */
export function FormattedDescription({ text }: FormattedDescriptionProps) {
  const trimmed = (text || '').trim();
  if (!trimmed) {
    return <p className="text-xs text-zinc-400">No description provided.</p>;
  }

  const lines = trimmed.split('\n');

  return (
    <div className="space-y-2 text-xs leading-relaxed text-zinc-700">
      {lines.map((rawLine, lineIdx) => {
        const line = rawLine.trim();
        if (!line) {
          return <div key={lineIdx} className="h-1" />;
        }
        if (line.startsWith('## ') || line.startsWith('### ')) {
          const headingText = line.replace(/^#{2,3}\s+/, '');
          return (
            <h4 key={lineIdx} className="pt-2 text-xs font-semibold text-zinc-950">
              {headingText}
            </h4>
          );
        }
        if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) {
          const bulletText = line.replace(/^[-*•]\s+/, '');
          return (
            <div key={lineIdx} className="flex gap-2 pl-2">
              <span className="text-emerald-600 select-none">•</span>
              <span>{renderInlineBold(bulletText)}</span>
            </div>
          );
        }
        return <p key={lineIdx}>{renderInlineBold(line)}</p>;
      })}
    </div>
  );
}
