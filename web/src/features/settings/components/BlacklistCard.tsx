import { useSignal } from '@preact/signals-react';
import { Ban, Plus, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { KEY_NAME } from '@/lib/constants';

/** Props for the dynamic blacklisted companies editor card. */
interface BlacklistCardProps {
  /** Current list of blacklisted company substrings. */
  companies: string[];
  /** Updates the blacklisted companies list. */
  onChange: (nextCompanies: string[]) => void;
}

/**
 * Tag-style editor for adding and removing blacklisted companies.
 */
export function BlacklistCard({ companies, onChange }: BlacklistCardProps) {
  const newBlacklist = useSignal('');

  const addBlacklist = () => {
    const clean = newBlacklist.value.trim().toLowerCase();
    if (!clean) return;
    if (!companies.includes(clean)) {
      onChange([...companies, clean]);
    }
    newBlacklist.value = '';
  };

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-800">
        <Ban className="h-3.5 w-3.5 text-red-500" />
        Blacklisted Companies
      </div>
      <div className="flex gap-2">
        <Input
          value={newBlacklist.value}
          onChange={event => {
            newBlacklist.value = event.target.value;
          }}
          onKeyDown={event => {
            if (event.key === KEY_NAME.ENTER) addBlacklist();
          }}
          placeholder="Add company name (e.g. micro1, outlier)..."
        />
        <Button variant="outline" onClick={addBlacklist}>
          <Plus className="h-3.5 w-3.5" />
          Add
        </Button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {companies.map(company => (
          <Badge key={company} variant="danger" className="gap-1.5 pr-1">
            {company}
            <button
              type="button"
              onClick={() => onChange(companies.filter(item => item !== company))}
              className="rounded hover:bg-red-200/70 p-0.5 cursor-pointer"
            >
              <X className="h-2.5 w-2.5" />
            </button>
          </Badge>
        ))}
      </div>
    </Card>
  );
}
