import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import type { UserSearchConfig } from '@/types';

/** Props for the filter thresholds configuration card. */
interface ThresholdsCardProps {
  /** Current search configuration draft. */
  draft: UserSearchConfig;
  /** Updates the configuration draft. */
  onChange: (next: UserSearchConfig) => void;
}

/**
 * Form card for editing seniority, remote-only, minimum match threshold, and max years experience.
 */
export function ThresholdsCard({ draft, onChange }: ThresholdsCardProps) {
  return (
    <Card className="p-4 space-y-3">
      <div className="text-xs font-semibold text-zinc-800">Filter Thresholds</div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <label className="space-y-1">
          <span className="text-zinc-500">Seniority Filter</span>
          <select
            value={draft.senioridade_filtro}
            onChange={event => onChange({ ...draft, senioridade_filtro: event.target.value })}
            className="h-8 w-full rounded-lg border border-zinc-200 bg-white px-2.5 text-xs"
          >
            <option value="JUNIOR">JUNIOR</option>
            <option value="PLENO">PLENO</option>
            <option value="SENIOR">SENIOR</option>
            <option value="ALL">ALL</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-zinc-500">Min Keyword Match (%)</span>
          <Input
            type="number"
            min={0}
            max={100}
            value={draft.threshold_minimo_match}
            onChange={event =>
              onChange({ ...draft, threshold_minimo_match: Number(event.target.value) })
            }
          />
        </label>
        <label className="space-y-1">
          <span className="text-zinc-500">Max Years Experience</span>
          <Input
            type="number"
            min={0}
            max={20}
            value={draft.max_anos_experiencia}
            onChange={event =>
              onChange({ ...draft, max_anos_experiencia: Number(event.target.value) })
            }
          />
        </label>
        <label className="flex items-center gap-2 pt-5 cursor-pointer">
          <input
            type="checkbox"
            checked={draft.apenas_remoto}
            onChange={event => onChange({ ...draft, apenas_remoto: event.target.checked })}
            className="accent-emerald-600"
          />
          <span className="text-zinc-700">Remote Only</span>
        </label>
      </div>
    </Card>
  );
}
