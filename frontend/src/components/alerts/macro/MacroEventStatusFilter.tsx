import { Bell, BellOff, List } from 'lucide-react'
import {
  AlertFilterGroup,
  type AlertFilterOption,
} from '@/components/alerts/shared/AlertFilterGroup'
import type { MacroEventStatusFilter as MacroEventStatusFilterValue } from '@/types/alerts/macroAlert'

export type MacroEventStatusCounts = Record<MacroEventStatusFilterValue, number>

type MacroEventStatusFilterProps = {
  value: MacroEventStatusFilterValue
  onChange: (value: MacroEventStatusFilterValue) => void
  counts: MacroEventStatusCounts
}

/** Same options and wording as the price alert filter. */
export function MacroEventStatusFilter({
  value,
  onChange,
  counts,
}: MacroEventStatusFilterProps) {
  const options: Array<AlertFilterOption<MacroEventStatusFilterValue>> = [
    { value: 'all', label: 'All', icon: List, count: counts.all },
    { value: 'active', label: 'Active', icon: Bell, count: counts.active },
    { value: 'inactive', label: 'Inactive', icon: BellOff, count: counts.inactive },
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
