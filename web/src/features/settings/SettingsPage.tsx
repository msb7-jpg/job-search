import { useSignal } from '@preact/signals-react';
import { useQuery } from '@tanstack/react-query';
import { Save } from 'lucide-react';
import { useUpdateConfig } from '@/api/mutations';
import { configQueries } from '@/api/queries';
import { Button } from '@/components/ui/button';
import type { UserSearchConfig } from '@/types';
import { BlacklistCard } from './components/BlacklistCard';
import { QueriesSkillsCard } from './components/QueriesSkillsCard';
import { ThresholdsCard } from './components/ThresholdsCard';

/**
 * Page orchestrator for editing search queries, skills, thresholds, and blacklisted companies.
 */
export function SettingsPage() {
  const { data } = useQuery(configQueries.get());
  const updateConfig = useUpdateConfig();

  const draftOverride = useSignal<UserSearchConfig | null>(null);
  const skillsTextOverride = useSignal<string | null>(null);

  const draft = draftOverride.value ?? data ?? null;
  const skillsText =
    skillsTextOverride.value ?? (data ? JSON.stringify(data.skills_map, null, 2) : '');

  if (!draft) {
    return <div className="p-6 text-xs text-zinc-400">Loading settings...</div>;
  }

  const handleSave = () => {
    try {
      const parsedSkills = JSON.parse(skillsText) as Record<string, string>;
      updateConfig.mutate({ ...draft, skills_map: parsedSkills });
    } catch {
      alert('Invalid JSON in Skills Map.');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">
            Search Queries, Filters & Company Blacklist
          </h2>
          <p className="text-xs text-zinc-500">
            Fully editable pipeline configuration — no hardcoded queries or blocked companies.
          </p>
        </div>
        <Button variant="primary" onClick={handleSave} disabled={updateConfig.isPending}>
          <Save className="h-3.5 w-3.5" />
          Save Settings
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ThresholdsCard
          draft={draft}
          onChange={next => {
            draftOverride.value = next;
          }}
        />
        <BlacklistCard
          companies={draft.blacklisted_companies}
          onChange={blacklisted_companies => {
            draftOverride.value = { ...draft, blacklisted_companies };
          }}
        />
        <QueriesSkillsCard
          draft={draft}
          skillsText={skillsText}
          onChangeDraft={next => {
            draftOverride.value = next;
          }}
          onChangeSkillsText={text => {
            skillsTextOverride.value = text;
          }}
        />
      </div>
    </div>
  );
}
