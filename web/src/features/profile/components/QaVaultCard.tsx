import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

/** Props for the Q&A Fact Vault key-value editor card. */
interface QaVaultCardProps {
  /** Key-value map of screening question answers. */
  qaVault: Record<string, string>;
  /** Updates the Q&A Fact Vault dictionary. */
  onChange: (nextVault: Record<string, string>) => void;
}

/**
 * Editable key-value store for common application screening questions.
 */
export function QaVaultCard({ qaVault, onChange }: QaVaultCardProps) {
  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-800">Q&A Fact Vault</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            const key = window.prompt('New Q&A key (e.g. notice_period):');
            if (key) {
              onChange({ ...qaVault, [key]: '' });
            }
          }}
        >
          <Plus className="h-3.5 w-3.5" />
          Add Field
        </Button>
      </div>
      <div className="space-y-2">
        {Object.entries(qaVault).map(([fieldKey, fieldValue]) => (
          <div key={fieldKey} className="grid grid-cols-12 items-center gap-2">
            <span className="col-span-5 truncate font-mono text-[11px] text-zinc-500">
              {fieldKey}
            </span>
            <Input
              className="col-span-7"
              value={fieldValue}
              onChange={event => onChange({ ...qaVault, [fieldKey]: event.target.value })}
            />
          </div>
        ))}
      </div>
    </Card>
  );
}
