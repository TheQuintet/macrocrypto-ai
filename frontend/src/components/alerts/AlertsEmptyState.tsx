import { BellPlus } from 'lucide-react'
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty'

/** Creating an alert is the page-level "Create alert" button's job. */
export function AlertsEmptyState() {
  return (
    <Empty className="min-h-[240px] border sm:min-h-[320px]">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <BellPlus />
        </EmptyMedia>
        <EmptyTitle>No alerts yet</EmptyTitle>
        <EmptyDescription>
          Use Create alert to set up your first one.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
