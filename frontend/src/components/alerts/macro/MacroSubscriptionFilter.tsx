import { Bell, BellOff, List } from 'lucide-react'
import {
  AlertFilterGroup,
  type AlertFilterOption,
} from '@/components/alerts/shared/AlertFilterGroup'
import type { MacroSubscriptionListFilter } from '@/types/alerts/macroAlert'

export type MacroSubscriptionCounts = Record<MacroSubscriptionListFilter, number>

type MacroSubscriptionFilterProps = {
  value: MacroSubscriptionListFilter
  onChange: (value: MacroSubscriptionListFilter) => void
  counts: MacroSubscriptionCounts
}

export function MacroSubscriptionFilter({
  value,
  onChange,
  counts,
}: MacroSubscriptionFilterProps) {
  const options: Array<AlertFilterOption<MacroSubscriptionListFilter>> = [
    { value: 'all', label: 'All', icon: List, count: counts.all },
    { value: 'subscribed', label: 'Subscribed', icon: Bell, count: counts.subscribed },
    {
      value: 'unsubscribed',
      label: 'Unsubscribed',
      icon: BellOff,
      count: counts.unsubscribed,
    },
  ]

  return (
    <AlertFilterGroup
      value={value}
      onChange={onChange}
      options={options}
      label="Filter events"
    />
  )
}
