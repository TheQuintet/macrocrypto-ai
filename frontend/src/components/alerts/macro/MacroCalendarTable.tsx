import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ConfirmationDialog } from '../shared/ConfirmationDialog';
import {
  Calendar,
  Filter,
  Clock,
  Repeat,
  Repeat1,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MacroEventSubscription } from '@/hooks/alerts/useMacroEvents';
import type {
  MacroEvent,
  EventImpact,
  EventType,
  MacroSubscriptionListFilter,
} from '@/types/alerts/macroAlert';
import {
  MACRO_EVENT_ICONS,
  MACRO_TIMING_LABELS,
} from './macroEventCopy';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select';

const impactBadgeColors: Record<EventImpact, string> = {
  HIGH: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};

const impactFilterLabels: Record<string, string> = {
  all: 'ALL IMPACTS',
  HIGH: '🔴 High',
  MEDIUM: '🟡 Medium',
  LOW: '🟢 Low',
};

interface MacroCalendarTableProps {
  events: MacroEvent[];
  subscriptions: Map<EventType, MacroEventSubscription>;
  isLoading: boolean;
  error: string | null;
  /** Subscription filter, driven by the toolbar above the table. */
  filter: MacroSubscriptionListFilter;
  onSubscribeChange: (eventId: string, subscribed: boolean) => void;
  onRetry: () => void;
}

export const MacroCalendarTable: React.FC<MacroCalendarTableProps> = ({
  events,
  subscriptions,
  isLoading,
  error,
  filter,
  onSubscribeChange,
  onRetry,
}) => {
  const [deletingEvent, setDeletingEvent] = useState<{ eventId: string; name: string } | null>(null);
  const [impactFilter, setImpactFilter] = useState<EventImpact | 'all'>('all');

  const filteredEvents = events.filter((event) => {
    if (filter === 'subscribed' && !event.subscribed) return false;
    if (filter === 'unsubscribed' && event.subscribed) return false;
    if (impactFilter !== 'all' && event.impact !== impactFilter) return false;
    return true;
  });

  const handleDelete = () => {
    if (!deletingEvent) return;
    onSubscribeChange(deletingEvent.eventId, false);
    setDeletingEvent(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.round((date.getTime() - now.getTime()) / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}d ${diffHours % 24}h left`;
    } else if (diffHours > 0) {
      return `${diffHours}h left`;
    } else {
      return '🔴 Now';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-0">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-16 w-full border-b last:border-0" />
          ))}
        </CardContent>
      </Card>
    );
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
    );
  }

  return (
    <>
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground min-w-[120px]">
                    Local Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground min-w-[100px]">
                    Time Left
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-muted-foreground min-w-[150px]">
                    Notify By
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground min-w-[180px]">
                    Event
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-muted-foreground min-w-[120px]">
                    <div className="flex items-center justify-center gap-1">
                      <Filter className="h-3 w-3" />
                      <Select
                        value={impactFilter}
                        onValueChange={(value) =>
                          setImpactFilter(value as EventImpact | 'all')
                        }
                      >
                        <SelectTrigger className="h-7 w-[120px] text-xs border-0 bg-transparent hover:bg-muted/50 focus:ring-0">
                          <span className="text-xs font-medium">
                            {impactFilterLabels[impactFilter as string]}
                          </span>
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">ALL IMPACTS</SelectItem>
                          <SelectItem value="HIGH">🔴 High</SelectItem>
                          <SelectItem value="MEDIUM">🟡 Medium</SelectItem>
                          <SelectItem value="LOW">🟢 Low</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-muted-foreground min-w-[100px]">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground min-w-[160px]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No events found matching your filters</p>
                    </td>
                  </tr>
                ) : (
                  filteredEvents.map((event) => {
                    const subData = subscriptions.get(event.event_type);
                    const eventTiming = subData?.timing;
                    const isOneTime = subData?.oneTime ?? true;
                    const isSubscribed = event.subscribed;
                    const hasNotifyBy = isSubscribed && eventTiming;

                    return (
                      <tr
                        key={event.id}
                        className="border-b last:border-0 hover:bg-muted/30 transition-colors"
                      >
                        <td className="px-4 py-3 text-sm">
                          {new Date(event.scheduled_at).toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">
                          {formatDate(event.scheduled_at)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {hasNotifyBy ? (
                            <div className="flex flex-col items-center gap-0.5">
                              <Badge variant="secondary" className="text-xs gap-1">
                                <Clock className="h-3 w-3" />
                                {MACRO_TIMING_LABELS[eventTiming]}
                              </Badge>
                              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                                {isOneTime ? (
                                  <>
                                    <Repeat1 className="h-2.5 w-2.5" />
                                    One-time
                                  </>
                                ) : (
                                  <>
                                    <Repeat className="h-2.5 w-2.5" />
                                    Recurring
                                  </>
                                )}
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{MACRO_EVENT_ICONS[event.event_type]}</span>
                            <div>
                              <p className="text-sm font-medium">{event.event_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {event.description}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge
                            variant="outline"
                            className={cn('text-xs', impactBadgeColors[event.impact])}
                          >
                            {event.impact}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {isSubscribed ? (
                            <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-0">
                              🔔 Subscribed
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-muted-foreground">
                              🔕 Unsubscribed
                            </Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant={isSubscribed ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => onSubscribeChange(event.id, !isSubscribed)}
                              className="h-7 text-xs"
                            >
                              {isSubscribed ? 'Unsubscribe' : 'Subscribe'}
                            </Button>
                            {isSubscribed && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                                onClick={() =>
                                  setDeletingEvent({
                                    eventId: event.id,
                                    name: event.event_name,
                                  })
                                }
                              >
                                <span className="sr-only">Delete</span>
                                ✕
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        open={!!deletingEvent}
        onOpenChange={() => setDeletingEvent(null)}
        onConfirm={handleDelete}
        title="Unsubscribe from Event"
        description={`Are you sure you want to unsubscribe from "${deletingEvent?.name}"?`}
        confirmText="Unsubscribe"
        variant="destructive"
      />
    </>
  );
};
