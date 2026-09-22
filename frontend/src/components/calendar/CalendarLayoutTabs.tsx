import { CalendarDays, List, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CalendarLayout } from '@/types/economicCalendar'

const TABS: Array<{ id: CalendarLayout; name: string; icon: LucideIcon }> = [
  { id: 'calendar', name: 'Calendar', icon: CalendarDays },
  { id: 'list', name: 'List', icon: List },
]

type CalendarLayoutTabsProps = {
  value: CalendarLayout
  onChange: (layout: CalendarLayout) => void
}

/** Primary switch between the month grid and the period table. */
export function CalendarLayoutTabs({
  value,
  onChange,
}: CalendarLayoutTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Calendar layout"
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
