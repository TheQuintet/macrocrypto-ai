import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type PriceAlertFormTab = 'alert' | 'advanced'

type PriceAlertFormTabsProps = {
  value: PriceAlertFormTab
  onChange: (tab: PriceAlertFormTab) => void
}

const TABS: Array<{ value: PriceAlertFormTab; label: string }> = [
  { value: 'alert', label: 'Alert' },
  { value: 'advanced', label: 'Advanced' },
]

export function PriceAlertFormTabs({ value, onChange }: PriceAlertFormTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Alert form sections"
      className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-1"
    >
      {TABS.map((tab) => (
        <Button
          key={tab.value}
          type="button"
          role="tab"
          size="sm"
          variant={value === tab.value ? 'default' : 'ghost'}
          aria-selected={value === tab.value}
          className={cn(
            'min-h-11 touch-manipulation sm:min-h-8',
            value !== tab.value && 'text-muted-foreground',
          )}
          onClick={() => onChange(tab.value)}
        >
          {tab.label}
        </Button>
      ))}
    </div>
  )
}
