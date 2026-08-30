import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { AlertListStatusFilter } from './shared/alertStatus'

type AlertStatusFilterProps = {
  value: AlertListStatusFilter
  onChange: (value: AlertListStatusFilter) => void
}

const OPTIONS: Array<{ value: AlertListStatusFilter; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

export function AlertStatusFilter({ value, onChange }: AlertStatusFilterProps) {
  return (
    <div
      className="flex w-full min-w-0 items-center gap-1 rounded-lg bg-muted p-1 sm:w-auto"
      role="group"
      aria-label="Filter alerts"
    >
      {OPTIONS.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={value === option.value ? 'default' : 'ghost'}
          aria-pressed={value === option.value}
          className={cn(
            'min-h-11 min-w-10 flex-1 touch-manipulation sm:min-h-8 sm:flex-none',
            value !== option.value && 'text-muted-foreground',
          )}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}
