import { Bell, BellOff, List } from 'lucide-react'
import { AlertFilterGroup, type AlertFilterOption } from './shared/AlertFilterGroup'
import type { AlertListStatusFilter } from './shared/alertStatus'

export type AlertStatusCounts = Record<AlertListStatusFilter, number>

type AlertStatusFilterProps = {
  value: AlertListStatusFilter
  onChange: (value: AlertListStatusFilter) => void
  counts: AlertStatusCounts
}

export function AlertStatusFilter({ value, onChange, counts }: AlertStatusFilterProps) {
  const options: Array<AlertFilterOption<AlertListStatusFilter>> = [
    { value: 'all', label: 'All', icon: List, count: counts.all },
    { value: 'active', label: 'Active', icon: Bell, count: counts.active },
    { value: 'inactive', label: 'Inactive', icon: BellOff, count: counts.inactive },
  ]

  return (
    <AlertFilterGroup
      value={value}
      onChange={onChange}
      options={options}
      label="Filter alerts"
    />
  )
}
