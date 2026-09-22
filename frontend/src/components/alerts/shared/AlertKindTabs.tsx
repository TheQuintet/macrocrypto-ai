import { Bell, Calendar, TrendingUp, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { alertKindTabClassName } from '@/lib/alerts/alertKindClassName'
import type { NewAlertType } from '@/types/alerts'

type AlertKindTabsProps = {
  value: NewAlertType
  onChange: (kind: NewAlertType) => void
  counts: Record<NewAlertType, number>
}

const TABS: Array<{ id: NewAlertType; name: string; icon: LucideIcon }> = [
  { id: 'price', name: 'Price Alerts', icon: Bell },
  { id: 'macro', name: 'Macro Alerts', icon: Calendar },
  { id: 'prediction', name: 'Prediction Alerts', icon: TrendingUp },
]

export function AlertKindTabs({ value, onChange, counts }: AlertKindTabsProps) {
  return (
    <>
      {TABS.map((tab) => {
        const active = value === tab.id
        const Icon = tab.icon
        const label = `${tab.name} (${counts[tab.id]})`

        return (
          <button
            key={tab.id}
            type="button"
            className={cn(
              'inline-flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              alertKindTabClassName(tab.id, active),
            )}
            onClick={() => onChange(tab.id)}
          >
            <Icon aria-hidden className="size-4 shrink-0" />
            {label}
          </button>
        )
      })}
    </>
  )
}
