import { Filter } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select'
import type { EventImpact } from '@/types/alerts/macroAlert'

export type ImpactFilterValue = EventImpact | 'all'

const IMPACT_LABELS: Record<ImpactFilterValue, string> = {
  all: 'All impacts',
  HIGH: '🔴 High',
  MEDIUM: '🟡 Medium',
  LOW: '🟢 Low',
}

type MacroImpactFilterProps = {
  value: ImpactFilterValue
  onChange: (value: ImpactFilterValue) => void
}

/** Impact filter, alongside the status filter now that the table has no header slot. */
export function MacroImpactFilter({ value, onChange }: MacroImpactFilterProps) {
  return (
    <Select value={value} onValueChange={(next: string) => onChange(next as ImpactFilterValue)}>
      <SelectTrigger
        aria-label="Filter by impact"
        className="h-9 w-[150px] gap-2 text-sm sm:h-8"
      >
        <span className="flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-muted-foreground" />
          {IMPACT_LABELS[value]}
        </span>
      </SelectTrigger>
      <SelectContent>
        {(Object.keys(IMPACT_LABELS) as ImpactFilterValue[]).map((impact) => (
          <SelectItem key={impact} value={impact}>
            {IMPACT_LABELS[impact]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
