import { BellPlus, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Empty,
  EmptyContent,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@/components/ui/empty'

type AlertsEmptyStateProps = {
  onCreateAlert: () => void
}

export function AlertsEmptyState({ onCreateAlert }: AlertsEmptyStateProps) {
  return (
    <Empty className="min-h-[240px] border sm:min-h-[320px]">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <BellPlus />
        </EmptyMedia>
        <EmptyTitle>No alerts yet</EmptyTitle>
      </EmptyHeader>
      <EmptyContent>
        <Button
          type="button"
          variant="outline"
          className="w-full sm:w-auto"
          onClick={onCreateAlert}
        >
          <Plus data-icon="inline-start" />
          New alert
        </Button>
      </EmptyContent>
    </Empty>
  )
}
