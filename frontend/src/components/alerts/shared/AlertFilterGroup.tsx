import type { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type AlertFilterOption<TValue extends string> = {
  value: TValue
  label: string
  icon: LucideIcon
  count: number
}

type AlertFilterGroupProps<TValue extends string> = {
  value: TValue
  onChange: (value: TValue) => void
  options: Array<AlertFilterOption<TValue>>
  label: string
}

/** Segmented filter shared by the price alert and macro event toolbars. */
export function AlertFilterGroup<TValue extends string>({
  value,
  onChange,
  options,
  label,
}: AlertFilterGroupProps<TValue>) {
  return (
    <div
      className="flex w-full min-w-0 items-center gap-1 rounded-lg bg-muted p-1 sm:w-auto"
      role="group"
      aria-label={label}
    >
      {options.map((option) => {
        const Icon = option.icon
        const isSelected = value === option.value

        return (
          <Button
            key={option.value}
            type="button"
            size="sm"
            variant={isSelected ? 'default' : 'ghost'}
            aria-pressed={isSelected}
            className={cn(
              'min-h-11 min-w-10 flex-1 touch-manipulation sm:min-h-8 sm:flex-none',
              !isSelected && 'text-muted-foreground',
            )}
            onClick={() => onChange(option.value)}
          >
            <Icon data-icon="inline-start" className="h-3.5 w-3.5" />
            {option.label} ({option.count})
          </Button>
        )
      })}
    </div>
  )
}
