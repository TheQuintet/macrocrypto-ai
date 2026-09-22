import { BellPlus } from 'lucide-react'
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty'

/** Creating an alert is the toolbar button's job, one per tab. */
export function AlertsEmptyState() {
  return (
    <Empty className="min-h-[240px] border sm:min-h-[320px]">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <BellPlus />
        </EmptyMedia>
        <EmptyTitle>No alerts yet</EmptyTitle>
        <EmptyDescription>
          Set up your first one from the button above.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
