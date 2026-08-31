import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { showToast } from '../shared/ToastNotification';
import { ConfirmationDialog } from '../shared/ConfirmationDialog';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MacroSubscription, EventType } from '@/types/alerts/macroAlert';
import { macroAlertApi } from '@/api/alerts/macroAlerts';

// Simple inline event item
const EventItem = ({
  name,
  impactLabel,
  impactColor,
  subscribed,
  onToggle,
}: {
  name: string;
  impactLabel: string;
  impactColor: string;
  subscribed: boolean;
  onToggle: () => void;
}) => {
  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg border transition-colors',
        subscribed ? 'border-primary/20 bg-primary/5' : 'border-border bg-background'
      )}
    >
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <span className="font-medium text-sm">{name}</span>
        <Badge variant="outline" className={cn('text-xs w-fit', impactColor)}>
          {impactLabel}
        </Badge>
      </div>
      <div className="flex items-center gap-3 pl-4 sm:pl-0">
        <span className="text-xs text-muted-foreground">
          {subscribed ? '✅ Subscribed' : '❌ Unsubscribed'}
        </span>
        <Switch checked={subscribed} onCheckedChange={onToggle} />
      </div>
    </div>
  );
};

interface MacroSubscriptionListProps {
  userId: string;
}

export const MacroSubscriptionList: React.FC<MacroSubscriptionListProps> = ({ userId }) => {
  const [subscriptions, setSubscriptions] = useState<MacroSubscription[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAllSubscribed, setIsAllSubscribed] = useState(false);
  const [highImpactOnly, setHighImpactOnly] = useState(false);
  const [pendingToggle, setPendingToggle] = useState<{
    eventType: EventType | 'ALL';
    subscribed: boolean;
    eventName: string;
  } | null>(null);
  const isMounted = useRef(true);
  const hasLoaded = useRef(false);

  const eventNames: Record<EventType, string> = {
    FED: 'Federal Reserve',
    CPI: 'Consumer Price Index',
    GDP: 'Gross Domestic Product',
    EMPLOYMENT: 'Employment Report',
  };

  const eventImpactLabels: Record<string, string> = {
    HIGH: 'High',
    MEDIUM: 'Medium',
    LOW: 'Low',
  };

  const eventImpactColors: Record<string, string> = {
    HIGH: 'text-red-500 border-red-500 bg-red-50 dark:bg-red-950/20',
    MEDIUM: 'text-yellow-500 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20',
    LOW: 'text-green-500 border-green-500 bg-green-50 dark:bg-green-950/20',
  };

  const filteredSubscriptions = useMemo(() => {
    if (!highImpactOnly) return subscriptions;
    return subscriptions.filter((s) => s.impact_filter === 'HIGH');
  }, [subscriptions, highImpactOnly]);

  const fetchSubscriptions = useCallback(async () => {
    if (!isMounted.current || hasLoaded.current) return;
    hasLoaded.current = true;
    setIsLoading(true);
    setError(null);
    try {
      const data = await macroAlertApi.getSubscriptions(); // ✅ No userId
      setSubscriptions(data);
      setIsAllSubscribed(data.every((s) => s.subscribed));
    } catch {
      setError('Failed to load subscriptions');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSubscriptions();
    }, 0);

    return () => {
      clearTimeout(timer);
      isMounted.current = false;
    };
  }, [fetchSubscriptions]);

  const handleToggle = async (eventType: EventType, subscribed: boolean) => {
    try {
      const updated = await macroAlertApi.updateSubscription(userId, eventType, subscribed);
      setSubscriptions((prev) =>
        prev.map((s) => (s.event_type === eventType ? updated : s))
      );
      setIsAllSubscribed(subscriptions.every((s) => s.subscribed));
      showToast.success(subscribed ? `${eventType} enabled` : `${eventType} disabled`);
    } catch {
      showToast.error('Failed to update subscription');
    }
  };

  const handleToggleClick = (eventType: EventType, subscribed: boolean, eventName: string) => {
    setPendingToggle({ eventType, subscribed, eventName });
  };

  const handleConfirmToggle = () => {
    if (pendingToggle) {
      if (pendingToggle.eventType === 'ALL') {
        handleToggleAll();
      } else {
        handleToggle(pendingToggle.eventType as EventType, pendingToggle.subscribed);
      }
      setPendingToggle(null);
    }
  };

  const handleToggleAll = async () => {
    const newState = !isAllSubscribed;
    try {
      const promises = subscriptions.map((s) =>
        macroAlertApi.updateSubscription(userId, s.event_type, newState)
      );
      const results = await Promise.all(promises);
      setSubscriptions(results);
      setIsAllSubscribed(newState);
      showToast.success(newState ? 'All events subscribed' : 'All events unsubscribed');
    } catch {
      showToast.error('Failed to update subscriptions');
    }
  };

  const handleToggleAllClick = () => {
    const newState = !isAllSubscribed;
    const eventName = newState ? 'subscribe to all events' : 'unsubscribe from all events';
    setPendingToggle({
      eventType: 'ALL',
      subscribed: newState,
      eventName,
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Macro Event Subscriptions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <AlertCircle className="h-8 w-8 mx-auto text-red-500 mb-2" />
          <p className="text-red-500">{error}</p>
          <Button variant="outline" className="mt-4" onClick={fetchSubscriptions}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <CardTitle>Macro Event Subscriptions</CardTitle>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">All Events</span>
            <Switch checked={isAllSubscribed} onCheckedChange={handleToggleAllClick} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">High Impact Only</span>
            <Switch
              checked={highImpactOnly}
              onCheckedChange={setHighImpactOnly}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {filteredSubscriptions.map((sub) => {
          const impact = sub.impact_filter || 'MEDIUM';
          return (
            <EventItem
              key={sub.event_type}
              name={eventNames[sub.event_type]}
              impactLabel={eventImpactLabels[impact]}
              impactColor={eventImpactColors[impact]}
              subscribed={sub.subscribed}
              onToggle={() => handleToggleClick(sub.event_type, !sub.subscribed, eventNames[sub.event_type])}
            />
          );
        })}
      </CardContent>

      <ConfirmationDialog
        open={!!pendingToggle}
        onOpenChange={() => setPendingToggle(null)}
        onConfirm={handleConfirmToggle}
        title="Confirm Subscription Change"
        description={`Are you sure you want to ${pendingToggle?.subscribed ? 'subscribe to' : 'unsubscribe from'} "${pendingToggle?.eventName}"?`}
        confirmText="Confirm"
        variant="default"
      />
    </Card>
  );
};