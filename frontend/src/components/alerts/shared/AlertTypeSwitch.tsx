import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { NewAlertType } from '@/types/alerts'

type AlertTypeSwitchProps = {
  value: NewAlertType
  onChange: (type: NewAlertType) => void
  disabled?: boolean
}

const TYPES: Array<{ value: NewAlertType; label: string }> = [
  { value: 'price', label: 'Price' },
  { value: 'macro', label: 'Macro event' },
]

/** Lets a half-filled create form change its mind about the alert kind. */
export function AlertTypeSwitch({ value, onChange, disabled = false }: AlertTypeSwitchProps) {
  return (
    <div role="group" aria-label="Alert type" className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">Alert for</span>
      <div className="flex flex-1 gap-1 rounded-lg border border-border p-1">
        {TYPES.map((type) => (
          <Button
            key={type.value}
            type="button"
            size="sm"
            variant={value === type.value ? 'secondary' : 'ghost'}
            aria-pressed={value === type.value}
            disabled={disabled}
            className={cn(
              'min-h-11 flex-1 touch-manipulation sm:min-h-8',
              value !== type.value && 'text-muted-foreground',
            )}
            onClick={() => onChange(type.value)}
          >
            {type.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
