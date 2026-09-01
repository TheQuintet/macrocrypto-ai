import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type AlertFormTab = 'alert' | 'advanced'

type AlertFormTabsProps = {
  value: AlertFormTab
  onChange: (tab: AlertFormTab) => void
}

const TABS: Array<{ value: AlertFormTab; label: string }> = [
  { value: 'alert', label: 'Alert' },
  { value: 'advanced', label: 'Advanced' },
]

export function AlertFormTabs({ value, onChange }: AlertFormTabsProps) {
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
