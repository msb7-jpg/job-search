import type { ReactNode } from 'react';

/** Props for the lightweight Markdown job description renderer. */
interface FormattedDescriptionProps {
  /** Markdown or plain-text job description content. */
  text: string;
}

/** Structured block parsed from Markdown job description lines. */
type DescriptionBlock =
  | { kind: 'heading'; text: string }
  | { kind: 'list'; items: string[] }
  | { kind: 'paragraph'; text: string };

const HEADING_PREFIX_RE = /^#{2,3}\s+/;
const BULLET_PREFIX_RE = /^[-*•]\s+/;

/**
 * Renders inline `**bold**` spans inside a description line, ensuring spacing when adjacent text lacks whitespace.
 */
function renderInlineBold(lineText: string): ReactNode[] {
  const parts = lineText.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    const isBold = part.startsWith('**') && part.endsWith('**') && part.length > 4;
    if (!isBold) {
      return part;
    }
    const nextPart = parts[idx + 1];
    const needsSpaceAfter = typeof nextPart === 'string' && /^[A-Za-zÀ-ÿ0-9]/.test(nextPart);
    return (
      <strong key={idx} className="font-semibold text-zinc-900">
        {part.slice(2, -2)}
        {needsSpaceAfter ? ' ' : ''}
      </strong>
    );
  });
}

/**
 * Groups raw Markdown lines into headings, compact bullet lists, and paragraphs.
 */
function parseDescriptionBlocks(rawText: string): DescriptionBlock[] {
  const blocks: DescriptionBlock[] = [];
  let pendingBullets: string[] = [];

  const flushBullets = () => {
    if (pendingBullets.length > 0) {
      blocks.push({ kind: 'list', items: pendingBullets });
      pendingBullets = [];
    }
  };

  for (const rawLine of rawText.split('\n')) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }
    if (HEADING_PREFIX_RE.test(line)) {
      flushBullets();
      blocks.push({ kind: 'heading', text: line.replace(HEADING_PREFIX_RE, '') });
      continue;
    }
    if (BULLET_PREFIX_RE.test(line)) {
      pendingBullets.push(line.replace(BULLET_PREFIX_RE, ''));
      continue;
    }
    flushBullets();
    blocks.push({ kind: 'paragraph', text: line });
  }
  flushBullets();
  return blocks;
}

/**
 * Renders scraped job descriptions with headings, compact bullet lists, bold spans, and paragraph spacing.
 */
export function FormattedDescription({ text }: FormattedDescriptionProps) {
  const trimmed = (text || '').trim();
  if (!trimmed) {
    return <p className="text-xs text-zinc-400">No description provided.</p>;
  }

  const blocks = parseDescriptionBlocks(trimmed);

  return (
    <div className="space-y-2.5 text-xs leading-relaxed text-zinc-700">
      {blocks.map((block, blockIdx) => {
        if (block.kind === 'heading') {
          return (
            <h4 key={blockIdx} className="pt-2 text-xs font-semibold text-zinc-950">
              {block.text}
            </h4>
          );
        }
        if (block.kind === 'list') {
          return (
            <ul key={blockIdx} className="space-y-1 pl-2">
              {block.items.map((item, itemIdx) => (
                <li key={itemIdx} className="flex gap-2">
                  <span className="text-emerald-600 select-none">•</span>
                  <span>{renderInlineBold(item)}</span>
                </li>
              ))}
            </ul>
          );
        }
        return <p key={blockIdx}>{renderInlineBold(block.text)}</p>;
      })}
    </div>
  );
}
