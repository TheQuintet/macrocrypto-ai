import { useMemo, useState } from 'react'
import { DateRangeFilter } from '@/components/alerts/shared/DateRangeFilter'
import { Pagination } from '@/components/alerts/shared/Pagination'
import { SearchBar } from '@/components/alerts/shared/SearchBar'
import { EventHistoryTable } from '@/components/calendar/EventHistoryTable'
import { pastEvents, searchEventHistory } from '@/lib/economicEventHistory'
import {
  EMPTY_DATE_RANGE,
  pageCount,
  paginate,
  type DateRange,
} from '@/lib/tableFilters'
import type { EconomicEvent } from '@/types/economicCalendar'

const PAGE_SIZE = 10

type EventHistoryProps = {
  /** Already narrowed by the calendar's event-type and impact filters. */
  events: EconomicEvent[]
  timeZone: string
  onSelectEvent: (event: EconomicEvent) => void
}

/**
 * Releases that have already happened, as a searchable table.
 *
 * The date range reads the event's own date, which is what the reader is
 * looking back over.
 */
export function EventHistory({
  events,
  timeZone,
  onSelectEvent,
}: EventHistoryProps) {
  const [search, setSearch] = useState('')
  const [dateRange, setDateRange] = useState<DateRange>(EMPTY_DATE_RANGE)
  const [page, setPage] = useState(1)

  const history = useMemo(() => pastEvents(events), [events])
  const visibleEvents = useMemo(
    () => searchEventHistory(history, { search, dateRange }, timeZone),
    [history, search, dateRange, timeZone],
  )

  const totalPages = pageCount(visibleEvents.length, PAGE_SIZE)
  const pageEvents = paginate(visibleEvents, page, PAGE_SIZE)

  return (
    <section
      aria-label="Past economic events"
      className="flex min-w-0 flex-col gap-3"
    >
      <div className="flex min-w-0 flex-col gap-3 lg:flex-row lg:items-end">
        <SearchBar
          value={search}
          onChange={(value) => {
            setSearch(value)
            setPage(1)
          }}
          placeholder="Search past events..."
          className="min-w-0 flex-1"
        />
        <DateRangeFilter
          startDate={dateRange.start}
          endDate={dateRange.end}
          onStartDateChange={(start) => {
            setDateRange((current) => ({ ...current, start }))
            setPage(1)
          }}
          onEndDateChange={(end) => {
            setDateRange((current) => ({ ...current, end }))
            setPage(1)
          }}
          className="min-w-0"
        />
      </div>

      <p className="text-xs text-muted-foreground">
        {visibleEvents.length}{' '}
        {visibleEvents.length === 1 ? 'event' : 'events'}
      </p>

      {visibleEvents.length === 0 ? (
        <p className="rounded-lg border border-border bg-card px-3 py-8 text-center text-sm text-muted-foreground">
          {history.length === 0
            ? 'No past events in the calendar yet.'
            : 'No past events match these filters.'}
        </p>
      ) : (
        <>
          <EventHistoryTable
            events={pageEvents}
            timeZone={timeZone}
            onSelectEvent={onSelectEvent}
          />

          {totalPages > 1 ? (
            <div className="flex justify-center pt-2">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            </div>
          ) : null}
        </>
      )}
    </section>
  )
}
