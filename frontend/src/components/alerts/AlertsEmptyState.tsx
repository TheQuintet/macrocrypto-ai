import { BellPlus, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty'

type AlertsEmptyStateProps = {
  onCreateAlert: () => void
}

/** Empty alerts placeholder with a create CTA. */
export function AlertsEmptyState({ onCreateAlert }: AlertsEmptyStateProps) {
  return (
    <Empty className="min-h-[240px] border sm:min-h-[320px]">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <BellPlus />
        </EmptyMedia>
        <EmptyTitle>No alerts yet</EmptyTitle>
        <EmptyDescription>
          You haven&apos;t created any alert rules. Add one to start tracking
          price moves and macro shifts.
        </EmptyDescription>
      </EmptyHeader>
      <EmptyContent>
        <Button
          type="button"
          variant="outline"
          className="w-full sm:w-auto"
          onClick={onCreateAlert}
        >
          <Plus data-icon="inline-start" />
          Create your first alert
        </Button>
      </EmptyContent>
    </Empty>
  )
}
