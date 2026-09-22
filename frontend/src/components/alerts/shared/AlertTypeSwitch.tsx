import { Bell, Calendar, TrendingUp } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { alertKindIconClassName } from '@/lib/alerts/alertKindClassName'
import type { NewAlertType } from '@/types/alerts'

type AlertTypeSwitchProps = {
  value: NewAlertType
  onChange: (type: NewAlertType) => void
  disabled?: boolean
}

const TYPES: Array<{ value: NewAlertType; label: string; icon: LucideIcon }> = [
  { value: 'price', label: 'Price alert', icon: Bell },
  { value: 'macro', label: 'Macro event alert', icon: Calendar },
  { value: 'prediction', label: 'Prediction alert', icon: TrendingUp },
]

/** Three icons — the whole alert-kind choice, without taking a row of its own. */
export function AlertTypeSwitch({ value, onChange, disabled = false }: AlertTypeSwitchProps) {
  return (
    <div
      role="group"
      aria-label="Alert type"
      className="flex shrink-0 items-center gap-0.5 rounded-lg bg-muted p-0.5"
    >
      {TYPES.map((type) => {
        const Icon = type.icon
        const isSelected = value === type.value

        return (
          <Button
            key={type.value}
            type="button"
            size="icon"
            variant="ghost"
            aria-label={type.label}
            aria-pressed={isSelected}
            title={type.label}
            disabled={disabled}
            className={cn('h-8 w-8', alertKindIconClassName(type.value, isSelected))}
            onClick={() => onChange(type.value)}
          >
            <Icon className="h-4 w-4" />
          </Button>
        )
      })}
    </div>
  )
}
