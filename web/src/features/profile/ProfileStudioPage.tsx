import { useSignal } from '@preact/signals-react';
import { useQuery } from '@tanstack/react-query';
import { Save } from 'lucide-react';
import { useParseResume, useUpdateConfig, useUpdateProfile } from '@/api/mutations';
import { configQueries, profileQueries } from '@/api/queries';
import { Button } from '@/components/ui/button';
import { TOAST_VARIANT } from '@/lib/constants';
import { showToast } from '@/state/signals';
import type { MasterProfile, ParsedResumeResult } from '@/types';
import { ExperiencePoolCard } from './components/ExperiencePoolCard';
import { IdentitySummaryCard } from './components/IdentitySummaryCard';
import { QaVaultCard } from './components/QaVaultCard';
import { ResumeImporterCard } from './components/ResumeImporterCard';

/**
 * Page orchestrator for importing/parsing resumes and editing the Master Profile.
 */
export function ProfileStudioPage() {
  const profileQuery = useQuery(profileQueries.get());
  const configQuery = useQuery(configQueries.get());
  const updateProfile = useUpdateProfile();
  const updateConfig = useUpdateConfig();
  const parseResume = useParseResume();

  const draftOverride = useSignal<MasterProfile | null>(null);
  const parsedPreview = useSignal<ParsedResumeResult | null>(null);

  const draft = draftOverride.value ?? profileQuery.data ?? null;
  if (!draft) {
    return <div className="p-6 text-xs text-zinc-400">Loading master profile...</div>;
  }

  const handleParse = (file: File | undefined, rawText: string | undefined) => {
    parseResume.mutate(
      { file, rawText },
      {
        onSuccess: res => {
          parsedPreview.value = res;
          draftOverride.value = res.profile;
          showToast('Resume parsed by LLM! Review & save below.');
        },
        onError: err => {
          showToast(
            err instanceof Error ? err.message : 'Failed to parse resume',
            TOAST_VARIANT.ERROR
          );
        },
      }
    );
  };

  const syncSuggestionsToConfig = () => {
    const preview = parsedPreview.value;
    if (!preview || !configQuery.data) return;
    const current = configQuery.data;
    const hasSkillsMap = Object.keys(preview.suggested_skills_map).length > 0;
    const hasRules = preview.suggested_scoring_rules.length > 0;
    const hasJobs = preview.suggested_queries_jobs.length > 0;
    const hasAts = preview.suggested_queries_ats.length > 0;
    const hasInhire = preview.suggested_inhire_terms.length > 0;

    updateConfig.mutate({
      ...current,
      primary_skill: preview.suggested_primary_skill ?? current.primary_skill,
      skills_map: hasSkillsMap ? preview.suggested_skills_map : current.skills_map,
      regras_pontuacao: hasRules ? preview.suggested_scoring_rules : current.regras_pontuacao,
      queries_jobs: hasJobs ? preview.suggested_queries_jobs : current.queries_jobs,
      queries_ats: hasAts ? preview.suggested_queries_ats : current.queries_ats,
      termos_cargo_inhire: hasInhire
        ? preview.suggested_inhire_terms
        : current.termos_cargo_inhire,
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">
            Master Profile & LLM Resume Parser
          </h2>
          <p className="text-xs text-zinc-500">
            Upload or paste any resume. The LLM structures it into editable bullets, skills, and search queries.
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => updateProfile.mutate(draft)}
          disabled={updateProfile.isPending}
        >
          <Save className="h-3.5 w-3.5" />
          Save Master Profile
        </Button>
      </div>

      <ResumeImporterCard
        isParsing={parseResume.isPending}
        hasParsedPreview={Boolean(parsedPreview.value)}
        onParse={handleParse}
        onSyncSuggestions={syncSuggestionsToConfig}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <IdentitySummaryCard
          draft={draft}
          onChange={next => {
            draftOverride.value = next;
          }}
        />
        <QaVaultCard
          qaVault={draft.qa_vault}
          onChange={qa_vault => {
            draftOverride.value = { ...draft, qa_vault };
          }}
        />
      </div>

      <ExperiencePoolCard
        experiences={draft.experiences}
        onChange={experiences => {
          draftOverride.value = { ...draft, experiences };
        }}
      />
    </div>
  );
}
