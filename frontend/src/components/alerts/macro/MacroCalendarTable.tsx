import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { showToast } from '../shared/ToastNotification';
import { ConfirmationDialog } from '../shared/ConfirmationDialog';
import {
  Calendar,
  Filter,
  Clock,
  Repeat,
  Repeat1,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { macroAlertApi } from '@/api/alerts/macroAlerts';
import type { MacroEvent, EventType, EventImpact } from '@/types/alerts/macroAlert';
import { MacroAlertForm } from './MacroAlertForm';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select';

type FilterType = 'all' | 'subscribed' | 'unsubscribed';

const impactBadgeColors: Record<EventImpact, string> = {
  HIGH: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};

const eventIcons: Record<EventType, string> = {
  FED: '🏛️',
  CPI: '📊',
  GDP: '📈',
  EMPLOYMENT: '👔',
};

const eventNames: Record<EventType, string> = {
  FED: 'Federal Reserve Meeting',
  CPI: 'CPI Release',
  GDP: 'GDP Release',
  EMPLOYMENT: 'Employment Report',
};

const timingLabels: Record<string, string> = {
  '1D': '1 day before',
  '12H': '12 hours before',
  '1H': '1 hour before',
};

const impactFilterLabels: Record<string, string> = {
  all: 'ALL IMPACTS',
  HIGH: '🔴 High',
  MEDIUM: '🟡 Medium',
  LOW: '🟢 Low',
};

interface MacroCalendarTableProps {
  userId: string;
}

export const MacroCalendarTable: React.FC<MacroCalendarTableProps> = ({ userId }) => {
  const [events, setEvents] = useState<MacroEvent[]>([]);
  const [subscriptions, setSubscriptions] = useState<Map<string, { timing: string; oneTime: boolean }>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterType>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deletingEvent, setDeletingEvent] = useState<{ eventId: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [impactFilter, setImpactFilter] = useState<EventImpact | 'all'>('all');

  useEffect(() => {
    const loadEvents = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await macroAlertApi.getUpcomingEvents();
        setEvents(data);
        const subs = await macroAlertApi.getSubscriptions();
        const timingMap = new Map<string, { timing: string; oneTime: boolean }>();
        subs.forEach((sub) => {
          timingMap.set(sub.event_type, {
            timing: sub.timing || '1D',
            oneTime: sub.one_time !== undefined ? sub.one_time : true,
          });
        });
        setSubscriptions(timingMap);
      } catch {
        setError('Failed to load events');
      } finally {
        setIsLoading(false);
      }
    };
    loadEvents();
  }, []);

  const filteredEvents = events.filter((event) => {
    if (filter === 'subscribed' && !event.subscribed) return false;
    if (filter === 'unsubscribed' && event.subscribed) return false;
    if (impactFilter !== 'all' && event.impact !== impactFilter) return false;
    return true;
  });

  const handleSubscribe = async (eventId: string, subscribe: boolean) => {
    try {
      const event = events.find((e) => e.id === eventId);
      if (!event) return;

      await macroAlertApi.updateSubscription(userId, event.event_type, subscribe);
      setEvents((prev) =>
        prev.map((e) =>
          e.id === eventId ? { ...e, subscribed: subscribe } : e
        )
      );
      showToast.success(subscribe ? 'Subscribed to event' : 'Unsubscribed from event');
    } catch {
      showToast.error('Failed to update subscription');
    }
  };

  const handleDelete = async () => {
    if (!deletingEvent) return;
    setIsDeleting(true);
    try {
      const event = events.find((e) => e.id === deletingEvent.eventId);
      if (event) {
        await macroAlertApi.updateSubscription(userId, event.event_type, false);
        setEvents((prev) =>
          prev.map((e) =>
            e.id === deletingEvent.eventId ? { ...e, subscribed: false } : e
          )
        );
        showToast.success(`${deletingEvent.name} unsubscribed`);
      }
      setDeletingEvent(null);
    } catch {
      showToast.error('Failed to unsubscribe');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCreateAlert = (
    eventType: EventType,
    timing: string,
    notifyInApp: boolean,
    notifyEmail: boolean,
    oneTime: boolean
  ) => {
    const event = events.find((e) => e.event_type === eventType);
    if (event) {
      setSubscriptions((prev) =>
        new Map(prev).set(eventType, { timing, oneTime })
      );
      handleSubscribe(event.id, true);
      showToast.success(
        `Alert set for ${eventNames[eventType]} (${timingLabels[timing]})${oneTime ? '' : ' (recurring)'}`
      );
      // TODO: Store notifyInApp and notifyEmail preferences
      if (notifyInApp) console.log('In-app notifications enabled');
      if (notifyEmail) console.log('Email notifications enabled');
    }
    setShowCreateModal(false);
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

  const totalEvents = events.length;
  const subscribedCount = events.filter((e) => e.subscribed).length;
  const unsubscribedCount = events.filter((e) => !e.subscribed).length;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <Card>
          <CardContent className="p-0">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16 w-full border-b last:border-0" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-red-500">{error}</p>
          <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold">Upcoming Events</h3>
          <Badge variant="secondary" className="text-xs">
            {filteredEvents.length} events
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1 p-1 rounded-lg bg-muted/50">
            <Button
              variant={filter === 'all' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setFilter('all')}
              className="h-7 text-xs"
            >
              All ({totalEvents})
            </Button>
            <Button
              variant={filter === 'subscribed' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setFilter('subscribed')}
              className="h-7 text-xs text-green-600"
            >
              🔔 Subscribed ({subscribedCount})
            </Button>
            <Button
              variant={filter === 'unsubscribed' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setFilter('unsubscribed')}
              className="h-7 text-xs text-muted-foreground"
            >
              🔕 Unsubscribed ({unsubscribedCount})
            </Button>
          </div>
          <Button size="sm" onClick={() => setShowCreateModal(true)}>
            <Calendar className="h-4 w-4 mr-2" />
            New Alert
          </Button>
        </div>
      </div>

      {/* Events Table */}
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
                                {timingLabels[eventTiming] || '1 day before'}
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
                            <span className="text-lg">{eventIcons[event.event_type]}</span>
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
                              onClick={() => handleSubscribe(event.id, !isSubscribed)}
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

      {/* Create Alert Modal */}
      <MacroAlertForm
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        userId={userId}
        events={events}
        onSubmit={handleCreateAlert}
      />

      {/* Delete Confirmation */}
      <ConfirmationDialog
        open={!!deletingEvent}
        onOpenChange={() => setDeletingEvent(null)}
        onConfirm={handleDelete}
        title="Unsubscribe from Event"
        description={`Are you sure you want to unsubscribe from "${deletingEvent?.name}"?`}
        confirmText="Unsubscribe"
        variant="destructive"
        isLoading={isDeleting}
      />
    </div>
  );
};