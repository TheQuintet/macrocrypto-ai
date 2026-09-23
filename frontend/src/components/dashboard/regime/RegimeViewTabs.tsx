import { BarChart3, GitCompare, History, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { RegimePageView } from '@/types/regime'

const TABS: Array<{ id: RegimePageView; name: string; icon: LucideIcon }> = [
  { id: 'performance', name: 'Performance', icon: BarChart3 },
  { id: 'timeline', name: 'Timeline', icon: History },
  { id: 'similarPeriods', name: 'Similar periods', icon: GitCompare },
]

type RegimeViewTabsProps = {
  value: RegimePageView
  onChange: (view: RegimePageView) => void
}

/** Primary switch between the three regime analysis views. */
export function RegimeViewTabs({ value, onChange }: RegimeViewTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Regime analysis views"
      className="flex border-b border-border"
    >
      {TABS.map((tab) => {
        const active = value === tab.id
        const Icon = tab.icon

        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            className={cn(
              'inline-flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              active
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
            onClick={() => onChange(tab.id)}
          >
            <Icon aria-hidden className="size-4 shrink-0" />
            {tab.name}
          </button>
        )
      })}
    </div>
  )
}
