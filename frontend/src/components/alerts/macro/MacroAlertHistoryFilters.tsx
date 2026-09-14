import { DateRangeFilter } from '@/components/alerts/shared/DateRangeFilter';
import { SearchBar } from '@/components/alerts/shared/SearchBar';
import { EVENT_TYPE_FILTER_OPTIONS } from '@/constants/economicCalendar';
import { cn } from '@/lib/utils';
import type { DateRange } from '@/lib/tableFilters';
import type { EventTypeFilter } from '@/types/economicCalendar';

type MacroAlertHistoryFiltersProps = {
  search: string;
  onSearchChange: (value: string) => void;
  eventType: EventTypeFilter;
  onEventTypeChange: (value: EventTypeFilter) => void;
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
};

/** Search, category, and a sent-date range — the three ways into a long history. */
export function MacroAlertHistoryFilters({
  search,
  onSearchChange,
  eventType,
  onEventTypeChange,
  dateRange,
  onDateRangeChange,
}: MacroAlertHistoryFiltersProps) {
  return (
    <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-end">
      <SearchBar
        value={search}
        onChange={onSearchChange}
        placeholder="Search sent alerts..."
        className="w-full min-w-0 sm:w-56"
      />

      <select
        aria-label="Event type filter"
        value={eventType}
        onChange={(event) =>
          onEventTypeChange(event.target.value as EventTypeFilter)
        }
        className={cn(
          'h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-2 text-sm sm:w-auto',
          'touch-manipulation outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
          'dark:bg-input/30',
        )}
      >
        {EVENT_TYPE_FILTER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <DateRangeFilter
        startDate={dateRange.start}
        endDate={dateRange.end}
        onStartDateChange={(start) => onDateRangeChange({ ...dateRange, start })}
        onEndDateChange={(end) => onDateRangeChange({ ...dateRange, end })}
        className="min-w-0"
      />
    </div>
  );
}
