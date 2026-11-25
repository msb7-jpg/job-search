import { Plus, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import type { ExperienceEntry } from '@/types';

/** Props for the Experience Bullet Pool editor card. */
interface ExperiencePoolCardProps {
  /** List of work experience entries with stable bullet IDs. */
  experiences: ExperienceEntry[];
  /** Updates the experience entries list. */
  onChange: (next: ExperienceEntry[]) => void;
}

/**
 * Editor for managing work experience roles and their deterministic bullet pools.
 */
export function ExperiencePoolCard({ experiences, onChange }: ExperiencePoolCardProps) {
  const addExperience = () => {
    onChange([
      ...experiences,
      {
        id: `exp_${Date.now()}`,
        company: 'New Company',
        role: 'Software Engineer',
        location: '',
        start_date: '',
        end_date: 'Present',
        bullets: [{ id: `bullet_${Date.now()}`, text: '', tags: [] }],
      },
    ]);
  };

  const updateExperience = (expIndex: number, patch: Partial<ExperienceEntry>) => {
    const next = [...experiences];
    const current = next[expIndex];
    if (!current) return;
    next[expIndex] = { ...current, ...patch };
    onChange(next);
  };

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-800">Experience Bullet Pool</span>
        <Button variant="outline" size="sm" onClick={addExperience}>
          <Plus className="h-3.5 w-3.5" />
          Add Experience
        </Button>
      </div>

      <div className="space-y-4">
        {experiences.map((exp, expIndex) => (
          <div key={exp.id} className="rounded-lg border border-zinc-200 p-3 space-y-2.5">
            <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
              <Input
                value={exp.role}
                placeholder="Role"
                onChange={event => updateExperience(expIndex, { role: event.target.value })}
              />
              <Input
                value={exp.company}
                placeholder="Company"
                onChange={event => updateExperience(expIndex, { company: event.target.value })}
              />
              <Input
                value={exp.start_date}
                placeholder="Start"
                onChange={event => updateExperience(expIndex, { start_date: event.target.value })}
              />
              <Input
                value={exp.end_date}
                placeholder="End"
                onChange={event => updateExperience(expIndex, { end_date: event.target.value })}
              />
              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onChange(experiences.filter((_exp, idx) => idx !== expIndex))}
                >
                  <Trash2 className="h-3.5 w-3.5 text-red-500" />
                </Button>
              </div>
            </div>

            <div className="space-y-1.5">
              {exp.bullets.map((bullet, bulletIndex) => (
                <div key={bullet.id} className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono shrink-0">
                    {bullet.id}
                  </Badge>
                  <Input
                    value={bullet.text}
                    onChange={event => {
                      const nextBullets = [...exp.bullets];
                      nextBullets[bulletIndex] = { ...bullet, text: event.target.value };
                      updateExperience(expIndex, { bullets: nextBullets });
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
