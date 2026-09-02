import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { EventImpactBadge } from '@/components/calendar/EventImpactBadge'
import { SubscriptionStatusBadge } from '@/components/calendar/SubscriptionStatusBadge'
import { EVENT_TYPE_LABELS } from '@/constants/economicCalendar'
import { routes } from '@/constants/navigation'
import { formatEventDateTime } from '@/lib/economicCalendarGrid'
import type { EconomicEvent } from '@/types/economicCalendar'

type EventDetailsDialogProps = {
  event: EconomicEvent | null
  subscribed: boolean | null
  timeZone: string
  onClose: () => void
}

function subscriptionSummary(subscribed: boolean | null): string {
  if (subscribed === null) {
    return 'Your subscriptions could not be loaded, so alert status is unknown.'
  }

  return subscribed
    ? 'You will be alerted before this event.'
    : 'You will not be alerted before this event.'
}

export function EventDetailsDialog({
  event,
  subscribed,
  timeZone,
  onClose,
}: EventDetailsDialogProps) {
  if (!event) {
    return null
  }

  return (
    <Dialog open onOpenChange={(open) => (open ? undefined : onClose())}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{event.event_name}</DialogTitle>
          <DialogDescription>
            {formatEventDateTime(event.event_date, timeZone)}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="px-2.5 py-0.5 text-sm">
              {EVENT_TYPE_LABELS[event.event_type] ?? event.event_type}
            </Badge>
            <EventImpactBadge impact={event.impact_level} />
            <SubscriptionStatusBadge subscribed={subscribed} />
          </div>

          {event.description ? (
            <p className="text-sm text-muted-foreground">
              {event.description}
            </p>
          ) : null}

          <p className="text-xs text-muted-foreground">
            {subscriptionSummary(subscribed)} Alert subscriptions are managed
            on the alerts page.
          </p>
        </div>

        <DialogFooter>
          <Button asChild variant="outline" size="sm">
            <Link to={routes.alerts}>Manage alerts</Link>
          </Button>
          <Button type="button" size="sm" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
