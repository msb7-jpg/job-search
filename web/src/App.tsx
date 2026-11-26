import type React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Ban,
  Inbox,
  Kanban,
  SlidersHorizontal,
  UserCheck,
} from 'lucide-react';
import { runQueries } from '@/api/queries';
import { ToastBanner } from '@/components/ToastBanner';
import { ProfileStudioPage } from '@/features/profile/ProfileStudioPage';
import { RejectionAuditPage } from '@/features/rejections/RejectionAuditPage';
import { ReviewStudioModal } from '@/features/review/ReviewStudioModal';
import { ScraperControlPage } from '@/features/scraper/ScraperControlPage';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { ApplicationTrackerPage } from '@/features/tracker/ApplicationTrackerPage';
import { TriageInboxPage } from '@/features/triage/TriageInboxPage';
import { APP_TAB } from '@/lib/constants';
import { cn } from '@/lib/utils';
import {
  type AppTab,
  activeTabSignal,
  studioJobIdSignal,
  toastSignal,
} from '@/state/signals';

const NAV_ITEMS: { id: AppTab; label: string; icon: typeof Inbox }[] = [
  { id: APP_TAB.TRIAGE, label: 'Inbox', icon: Inbox },
  { id: APP_TAB.TRACKER, label: 'Tracker', icon: Kanban },
  { id: APP_TAB.REJECTIONS, label: 'Audit Log', icon: Ban },
  { id: APP_TAB.SCRAPER, label: 'Scraper', icon: Activity },
  { id: APP_TAB.PROFILE, label: 'Profile', icon: UserCheck },
  { id: APP_TAB.SETTINGS, label: 'Settings', icon: SlidersHorizontal },
];

/**
 * Renders the active feature page for the selected navigation tab.
 */
function renderTabContent(activeTab: AppTab) {
  const tabMap = new Map<AppTab, () => React.ReactNode>([
    [APP_TAB.TRIAGE, () => <TriageInboxPage />],
    [APP_TAB.TRACKER, () => <ApplicationTrackerPage />],
    [APP_TAB.REJECTIONS, () => <RejectionAuditPage />],
    [APP_TAB.SCRAPER, () => <ScraperControlPage />],
    [APP_TAB.PROFILE, () => <ProfileStudioPage />],
    [APP_TAB.SETTINGS, () => <SettingsPage />],
  ]);
  return tabMap.get(activeTab)?.() ?? null;
}

/**
 * Root Command Center shell orchestrating top-level navigation tabs, Review Studio modal, and toast feedback.
 */
export default function App() {
  const activeTab = activeTabSignal.value;
  const studioJobId = studioJobIdSignal.value;
  const runsQuery = useQuery(runQueries.overview());
  const pendingCount = runsQuery.data?.pending_llm_count ?? 0;

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#09090B]">
      <header className="sticky top-0 z-30 border-b border-zinc-200/80 bg-white/85 backdrop-blur-md">
        <div className="mx-auto flex h-13 max-w-[1440px] items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
            </div>
            <span className="text-sm font-semibold tracking-tight text-zinc-950">JobSearch</span>

          </div>

          <nav className="flex items-center gap-1 overflow-x-auto">
            {NAV_ITEMS.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              const showPendingBadge = item.id === 'scraper' && pendingCount > 0;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    activeTabSignal.value = item.id;
                  }}
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap',
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200/80'
                      : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950 border border-transparent'
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {item.label}
                  {showPendingBadge && (
                    <span className="rounded-full bg-amber-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-amber-800">
                      {pendingCount}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] p-4 sm:p-6">
        {renderTabContent(activeTab)}
      </main>

      {studioJobId !== null && <ReviewStudioModal jobId={studioJobId} />}
      <ToastBanner
        toast={toastSignal.value}
        onDismiss={() => {
          toastSignal.value = null;
        }}
      />
    </div>
  );
}
