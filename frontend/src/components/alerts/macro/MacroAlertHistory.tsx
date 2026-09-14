import { useMemo, useState } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertListToolbar } from '@/components/alerts/shared/AlertListToolbar';
import { Pagination } from '@/components/alerts/shared/Pagination';
import { showToast } from '@/components/alerts/shared/ToastNotification';
import { MacroAlertHistoryFilters } from '@/components/alerts/macro/MacroAlertHistoryFilters';
import { MacroAlertHistoryTable } from '@/components/alerts/macro/MacroAlertHistoryTable';
import { useMacroAlertHistoryQuery } from '@/hooks/alerts/useMacroAlertHistoryQuery';
import { displayTimezone } from '@/lib/economicCalendarGrid';
import {
  filterMacroAlertHistory,
  macroAlertHistoryToCsv,
  sortMacroAlertHistory,
} from '@/lib/alerts/macroAlertHistoryFilters';
import { downloadTextFile } from '@/lib/downloadFile';
import {
  EMPTY_DATE_RANGE,
  pageCount,
  paginate,
  type DateRange,
} from '@/lib/tableFilters';
import type { EventTypeFilter } from '@/types/economicCalendar';

const PAGE_SIZE = 10;

type MacroAlertHistoryProps = {
  userId: string;
};

/**
 * Macro event alerts that were actually sent to this user.
 *
 * Filtering, search, and pagination all run over the rows the view holds, so
 * a search covers the whole loaded history rather than whichever page the
 * reader happens to be on.
 */
export function MacroAlertHistory({ userId }: MacroAlertHistoryProps) {
  const [search, setSearch] = useState('');
  const [eventType, setEventType] = useState<EventTypeFilter>('all');
  const [dateRange, setDateRange] = useState<DateRange>(EMPTY_DATE_RANGE);
  const [page, setPage] = useState(1);

  const timeZone = useMemo(() => displayTimezone('local'), []);
  const historyQuery = useMacroAlertHistoryQuery(userId);

  const entries = useMemo(
    () => sortMacroAlertHistory(historyQuery.data?.notifications ?? []),
    [historyQuery.data],
  );

  const visibleEntries = useMemo(
    () =>
      filterMacroAlertHistory(
        entries,
        { search, eventType, dateRange },
        timeZone,
      ),
    [entries, search, eventType, dateRange, timeZone],
  );

  const totalPages = pageCount(visibleEntries.length, PAGE_SIZE);
  const pageEntries = paginate(visibleEntries, page, PAGE_SIZE);

  /** Any change to what is being filtered puts the reader back on page one. */
  const resetPage = () => setPage(1);

  const handleExport = () => {
    const csv = macroAlertHistoryToCsv(visibleEntries, timeZone);
    const saved = downloadTextFile('macro-alert-history.csv', csv);

    if (saved) {
      showToast.success(
        `Exported ${visibleEntries.length} ${
          visibleEntries.length === 1 ? 'alert' : 'alerts'
        }`,
      );
    } else {
      showToast.error('This browser cannot download the export');
    }
  };

  const summary =
    visibleEntries.length === entries.length
      ? `${entries.length} sent ${entries.length === 1 ? 'alert' : 'alerts'}`
      : `${visibleEntries.length} of ${entries.length} sent alerts`;

  const total = historyQuery.data?.total ?? entries.length;
  const isCapped = total > entries.length;

  if (historyQuery.isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Macro alert history</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-9 w-full" />
          {[1, 2, 3, 4].map((row) => (
            <Skeleton key={row} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (historyQuery.error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p role="alert" className="mb-2 text-sm text-destructive">
            Failed to load macro alert history
          </p>
          <p className="text-sm text-muted-foreground">
            {historyQuery.error.message}
          </p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => historyQuery.refetch()}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle>Macro alert history</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={handleExport}
          disabled={visibleEntries.length === 0}
        >
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        <AlertListToolbar summary={summary}>
          <MacroAlertHistoryFilters
            search={search}
            onSearchChange={(value) => {
              setSearch(value);
              resetPage();
            }}
            eventType={eventType}
            onEventTypeChange={(value) => {
              setEventType(value);
              resetPage();
            }}
            dateRange={dateRange}
            onDateRangeChange={(range) => {
              setDateRange(range);
              resetPage();
            }}
          />
        </AlertListToolbar>

        {isCapped ? (
          <p className="text-xs text-muted-foreground">
            Showing the most recent {entries.length} of {total} sent alerts.
          </p>
        ) : null}

        {entries.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No macro alerts have been sent yet.
          </p>
        ) : visibleEntries.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No sent alerts match these filters.
          </p>
        ) : (
          <>
            <MacroAlertHistoryTable
              entries={pageEntries}
              timeZone={timeZone}
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
      </CardContent>
    </Card>
  );
}
