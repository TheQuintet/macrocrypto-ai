import { cn } from '@/lib/utils'
import {
  alertKindDotClassName,
  alertKindTabClassName,
} from '@/lib/alerts/alertKindClassName'
import type { NewAlertType } from '@/types/alerts'

type AlertKindTab = {
  id: NewAlertType
  label: string
  count: number
}

type AlertKindTabsProps = {
  value: NewAlertType
  onChange: (kind: NewAlertType) => void
  counts: Record<NewAlertType, number>
}

const TABS: Array<{ id: NewAlertType; name: string }> = [
  { id: 'price', name: 'Price Alerts' },
  { id: 'macro', name: 'Macro Alerts' },
  { id: 'prediction', name: 'Prediction Alerts' },
]

export function AlertKindTabs({ value, onChange, counts }: AlertKindTabsProps) {
  const tabs: AlertKindTab[] = TABS.map((tab) => ({
    id: tab.id,
    label: `${tab.name} (${counts[tab.id]})`,
    count: counts[tab.id],
  }))

  return (
    <>
      {tabs.map((tab) => {
        const active = value === tab.id
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
            <span
              aria-hidden
              className={cn('size-2.5 shrink-0 rounded-full', alertKindDotClassName(tab.id))}
            />
            {tab.label}
          </button>
        )
      })}
    </>
  )
}
