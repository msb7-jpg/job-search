import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

/** Props for the Triage Inbox search and provider filter toolbar. */
interface TriageToolbarProps {
  /** Current search query text. */
  searchInput: string;
  /** Currently selected provider filter, or empty string for all. */
  providerFilter: string;
  /** Distinct provider names present in the inbox. */
  providers: string[];
  /** Updates the search query signal. */
  onSearchChange: (value: string) => void;
  /** Updates the provider filter signal. */
  onProviderChange: (value: string) => void;
}

/**
 * Top filter bar and keyboard shortcut legend for the Triage Inbox.
 */
export function TriageToolbar({
  searchInput,
  providerFilter,
  providers,
  onSearchChange,
  onProviderChange,
}: TriageToolbarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <div className="relative w-64">
          <Search className="pointer-events-none absolute left-2.5 top-2 h-3.5 w-3.5 text-zinc-400" />
          <Input
            value={searchInput}
            onChange={event => onSearchChange(event.target.value)}
            placeholder="Search title, company, stack..."
            className="pl-8"
          />
        </div>
        <select
          value={providerFilter}
          onChange={event => onProviderChange(event.target.value)}
          className="h-8 rounded-lg border border-zinc-200 bg-white px-2.5 text-xs text-zinc-700 focus:border-emerald-500 focus:outline-none"
        >
          <option value="">All providers</option>
          {providers.map(provider => (
            <option key={provider} value={provider}>
              {provider}
            </option>
          ))}
        </select>
      </div>

      <div className="hidden items-center gap-3 font-mono text-[11px] text-zinc-400 md:flex">
        <span>[J/K] Navigate</span>
        <span>[S] Save</span>
        <span>[T] Tailor</span>
        <span>[X] Ignore</span>
        <span>[O] Open</span>
      </div>
    </div>
  );
}
