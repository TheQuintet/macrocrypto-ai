import { useCallback, useMemo, useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { CalendarAgenda } from '@/components/calendar/CalendarAgenda'
import { CalendarGrid } from '@/components/calendar/CalendarGrid'
import { CalendarLayoutTabs } from '@/components/calendar/CalendarLayoutTabs'
import { CalendarToolbar } from '@/components/calendar/CalendarToolbar'
import { EconomicEventList } from '@/components/calendar/EconomicEventList'
import { EventDetailsDialog } from '@/components/calendar/EventDetailsDialog'
import { useMacroSubscriptionsQuery } from '@/hooks/alerts/useMacroSubscriptionsQuery'
import { useEconomicCalendarQuery } from '@/hooks/useEconomicCalendarQuery'
import {
  anchorForInstant,
  buildCalendarGrid,
  displayTimezone,
  eventsInCurrentPeriod,
  shiftAnchor,
  startOfMonth,
  startOfWeek,
} from '@/lib/economicCalendarGrid'
import {
  activeSubscriptionsByType,
  filterEconomicEvents,
  isEventSubscribed,
} from '@/lib/economicEventFilters'
import type {
  CalendarLayout,
  CalendarTimezoneMode,
  CalendarViewMode,
  EconomicEvent,
  EventTypeFilter,
  ImpactLevelFilter,
} from '@/types/economicCalendar'

type EconomicCalendarProps = {
  userId: string
}

export function EconomicCalendar({ userId }: EconomicCalendarProps) {
  const [view, setView] = useState<CalendarViewMode>('month')
  const [layout, setLayout] = useState<CalendarLayout>('calendar')
  const [timezoneMode, setTimezoneMode] =
    useState<CalendarTimezoneMode>('local')
  const [eventType, setEventType] = useState<EventTypeFilter>('all')
  const [impactLevel, setImpactLevel] = useState<ImpactLevelFilter>('all')
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null)
  const [anchor, setAnchor] = useState(() =>
    anchorForInstant(new Date(), 'month', displayTimezone('local')),
  )

  const timeZone = useMemo(
    () => displayTimezone(timezoneMode),
    [timezoneMode],
  )

  const calendarQuery = useEconomicCalendarQuery()
  const subscriptionsQuery = useMacroSubscriptionsQuery(userId)

  const events = useMemo(() => calendarQuery.data ?? [], [calendarQuery.data])
  const visibleEvents = useMemo(
    () => filterEconomicEvents(events, { eventType, impactLevel }),
    [events, eventType, impactLevel],
  )
  const grid = useMemo(
    () =>
      buildCalendarGrid({
        anchor,
        view,
        events: visibleEvents,
        timeZone,
      }),
    [anchor, view, visibleEvents, timeZone],
  )
  const periodEvents = useMemo(
    () => eventsInCurrentPeriod(grid),
    [grid],
  )

  const subscriptionsByType = useMemo(
    () => activeSubscriptionsByType(subscriptionsQuery.data ?? []),
    [subscriptionsQuery.data],
  )

  /**
   * `null` while subscriptions are loading or after they failed — the calendar
   * says "unknown" rather than badging every event as unsubscribed.
   */
  const subscriptionsKnown =
    !subscriptionsQuery.isPending && !subscriptionsQuery.error
  const isSubscribed = useCallback(
    (event: EconomicEvent): boolean | null =>
      subscriptionsKnown
        ? isEventSubscribed(event, subscriptionsByType)
        : null,
    [subscriptionsKnown, subscriptionsByType],
  )

  const selectedEvent =
    events.find((event) => event.id === selectedEventId) ?? null
  const isSimulated = events.some(
    (event) => event.dataSource === 'simulated',
  )

  const handleViewChange = (nextView: CalendarViewMode) => {
    setView(nextView)
    setAnchor((current) =>
      nextView === 'month' ? startOfMonth(current) : startOfWeek(current),
    )
  }

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <CalendarLayoutTabs value={layout} onChange={setLayout} />

      <CalendarToolbar
        label={grid.label}
        view={view}
        onViewChange={handleViewChange}
        timezoneMode={timezoneMode}
        onTimezoneModeChange={setTimezoneMode}
        timeZone={displayTimezone('local')}
        eventType={eventType}
        onEventTypeChange={setEventType}
        impactLevel={impactLevel}
        onImpactLevelChange={setImpactLevel}
        onPrevious={() =>
          setAnchor((current) => shiftAnchor(current, view, -1))
        }
        onNext={() =>
          setAnchor((current) => shiftAnchor(current, view, 1))
        }
        isSimulated={isSimulated}
      />

      {subscriptionsQuery.error ? (
        <p className="rounded-lg border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
          Alert subscriptions could not be loaded, so the calendar cannot show
          which events you are subscribed to.
        </p>
      ) : null}

      {calendarQuery.isPending ? (
        <Skeleton className="h-96 w-full rounded-lg" />
      ) : calendarQuery.error ? (
        <p
          role="alert"
          className="rounded-lg border border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground"
        >
          Economic calendar unavailable. {calendarQuery.error.message}
        </p>
      ) : (
        layout === 'list' ? (
          <EconomicEventList
            events={periodEvents}
            periodLabel={grid.label}
            timeZone={timeZone}
            isSubscribed={isSubscribed}
            onSelectEvent={(event) => setSelectedEventId(event.id)}
          />
        ) : (
          <>
            <CalendarGrid
              grid={grid}
              timeZone={timeZone}
              isSubscribed={isSubscribed}
              onSelectEvent={(event) => setSelectedEventId(event.id)}
            />
            <CalendarAgenda
              grid={grid}
              timeZone={timeZone}
              isSubscribed={isSubscribed}
              onSelectEvent={(event) => setSelectedEventId(event.id)}
            />
          </>
        )
      )}

      {grid.undated.length > 0 ? (
        <p className="text-xs text-muted-foreground">
          {grid.undated.length} event
          {grid.undated.length === 1 ? '' : 's'} could not be placed on the
          calendar because the feed sent an unreadable date.
        </p>
      ) : null}

      <EventDetailsDialog
        event={selectedEvent}
        subscribed={selectedEvent ? isSubscribed(selectedEvent) : null}
        timeZone={timeZone}
        onClose={() => setSelectedEventId(null)}
      />
    </div>
  )
}
