import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Calendar } from 'lucide-react'
import { ConfirmationDialog } from '../shared/ConfirmationDialog'
import { AlertTable } from '../shared/AlertTable'
import { AlertTableEmptyRow } from '../shared/AlertTableEmptyRow'
import { MacroEventRow } from './MacroEventRow'
import type { MacroEventSubscription } from '@/hooks/alerts/useMacroEvents'
import type {
  EventImpact,
  EventType,
  MacroEvent,
  MacroEventStatusFilter,
} from '@/types/alerts/macroAlert'

type MacroCalendarTableProps = {
  events: MacroEvent[]
  subscriptions: Map<EventType, MacroEventSubscription>
  isLoading: boolean
  error: string | null
  /** Filters live in the toolbar above the table. */
  filter: MacroEventStatusFilter
  impactFilter: EventImpact | 'all'
  onSubscribeChange: (eventId: string, subscribed: boolean) => void
  onDelete: (eventId: string) => void
  onEdit: (event: MacroEvent) => void
  onRetry: () => void
}

export function MacroCalendarTable({
  events,
  subscriptions,
  isLoading,
  error,
  filter,
  impactFilter,
  onSubscribeChange,
  onDelete,
  onEdit,
  onRetry,
}: MacroCalendarTableProps) {
  const [deletingEvent, setDeletingEvent] = useState<{ eventId: string; name: string } | null>(
    null,
  )

  const filteredEvents = events.filter((event) => {
    if (filter === 'active' && !event.subscribed) return false
    if (filter === 'inactive' && event.subscribed) return false
    if (impactFilter !== 'all' && event.impact !== impactFilter) return false
    return true
  })

  const handleDelete = () => {
    if (!deletingEvent) return
    onDelete(deletingEvent.eventId)
    setDeletingEvent(null)
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-0">
          {[1, 2, 3, 4].map((row) => (
            <Skeleton key={row} className="h-16 w-full border-b last:border-0" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-red-500">{error}</p>
          <Button variant="outline" className="mt-4" onClick={onRetry}>
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <AlertTable nameLabel="Event" detailLabel="When">
        {filteredEvents.length === 0 ? (
          <AlertTableEmptyRow
            icon={Calendar}
            message="No events found matching your filters"
          />
        ) : (
          filteredEvents.map((event) => (
            <MacroEventRow
              key={event.id}
              event={event}
              subscription={subscriptions.get(event.event_type)}
              onSubscribeChange={onSubscribeChange}
              onEdit={onEdit}
              onDelete={(eventId) =>
                setDeletingEvent({ eventId, name: event.event_name })
              }
            />
          ))
        )}
      </AlertTable>

      <ConfirmationDialog
        open={!!deletingEvent}
        onOpenChange={() => setDeletingEvent(null)}
        onConfirm={handleDelete}
        title="Delete alert"
        description={`This removes the alert for "${deletingEvent?.name}". This cannot be undone.`}
        confirmText="Delete"
        variant="destructive"
      />
    </>
  )
}
