import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import type { MasterProfile } from '@/types';

/** Props for the candidate identity and default summary card. */
interface IdentitySummaryCardProps {
  /** Current `MasterProfile` draft. */
  draft: MasterProfile;
  /** Updates the `MasterProfile` draft. */
  onChange: (next: MasterProfile) => void;
}

/**
 * Editable form card for immutable candidate contact facts and base summary.
 */
export function IdentitySummaryCard({ draft, onChange }: IdentitySummaryCardProps) {
  const updateIdentity = (field: keyof MasterProfile['identity'], value: string) => {
    onChange({ ...draft, identity: { ...draft.identity, [field]: value } });
  };

  return (
    <Card className="p-4 space-y-3">
      <div className="text-xs font-semibold text-zinc-800">Identity</div>
      <div className="grid grid-cols-2 gap-2.5">
        <Input
          placeholder="Full Name"
          value={draft.identity.full_name}
          onChange={event => updateIdentity('full_name', event.target.value)}
        />
        <Input
          placeholder="Headline"
          value={draft.identity.headline}
          onChange={event => updateIdentity('headline', event.target.value)}
        />
        <Input
          placeholder="Email"
          value={draft.identity.email}
          onChange={event => updateIdentity('email', event.target.value)}
        />
        <Input
          placeholder="Location"
          value={draft.identity.location}
          onChange={event => updateIdentity('location', event.target.value)}
        />
        <Input
          placeholder="LinkedIn URL"
          value={draft.identity.linkedin_url}
          onChange={event => updateIdentity('linkedin_url', event.target.value)}
        />
        <Input
          placeholder="GitHub URL"
          value={draft.identity.github_url}
          onChange={event => updateIdentity('github_url', event.target.value)}
        />
      </div>
      <div className="space-y-1">
        <span className="text-[11px] font-medium text-zinc-500">Default Summary</span>
        <Textarea
          rows={3}
          value={draft.default_summary}
          onChange={event => onChange({ ...draft, default_summary: event.target.value })}
        />
      </div>
    </Card>
  );
}
