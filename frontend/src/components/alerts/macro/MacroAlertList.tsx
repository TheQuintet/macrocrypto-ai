import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { showToast } from '../shared/ToastNotification';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MacroSubscription, EventType } from '@/types/alerts/macroAlert';
import { macroAlertApi } from '@/api/alerts/macroAlerts';

type FilterType = 'all' | 'subscribed' | 'unsubscribed';

// Simple event item component
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
  onToggle: (checked: boolean) => void;
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
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">
          {subscribed ? '✅ Subscribed' : '❌ Unsubscribed'}
        </span>
        <Switch checked={subscribed} onCheckedChange={onToggle} />
      </div>
    </div>
  );
};

interface MacroAlertListProps {
  userId: string;
}

export const MacroAlertList: React.FC<MacroAlertListProps> = ({ userId }) => {
  const [subscriptions, setSubscriptions] = useState<MacroSubscription[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterType>('all');
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
    if (filter === 'all') return subscriptions;
    if (filter === 'subscribed') return subscriptions.filter((s) => s.subscribed);
    return subscriptions.filter((s) => !s.subscribed);
  }, [subscriptions, filter]);

  const loadSubscriptions = useCallback(async () => {
    if (!isMounted.current || hasLoaded.current) return;
    hasLoaded.current = true;
    setIsLoading(true);
    setError(null);
    try {
      const data = await macroAlertApi.getSubscriptions(userId);
      if (isMounted.current) {
        setSubscriptions(data);
      }
    } catch {
      if (isMounted.current) {
        setError('Failed to load subscriptions');
      }
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [userId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadSubscriptions();
    }, 0);

    return () => {
      clearTimeout(timer);
      isMounted.current = false;
    };
  }, [loadSubscriptions]);

  const handleToggle = async (eventType: EventType, subscribed: boolean) => {
    try {
      const updated = await macroAlertApi.updateSubscription(userId, eventType, subscribed);
      setSubscriptions((prev) =>
        prev.map((s) => (s.event_type === eventType ? updated : s))
      );
      showToast.success(subscribed ? `${eventType} enabled` : `${eventType} disabled`);
    } catch {
      showToast.error('Failed to update subscription');
    }
  };

  const handleRefresh = () => {
    hasLoaded.current = false;
    loadSubscriptions();
    showToast.info('Refreshing...');
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Macro Alerts</CardTitle>
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
          <Button variant="outline" className="mt-4" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <CardTitle>Macro Alerts ({subscriptions.length})</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1">
            <Button
              variant={filter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              All
            </Button>
            <Button
              variant={filter === 'subscribed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('subscribed')}
              className="text-green-600"
            >
              Subscribed
            </Button>
            <Button
              variant={filter === 'unsubscribed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('unsubscribed')}
              className="text-gray-600"
            >
              Unsubscribed
            </Button>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={cn('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {filteredSubscriptions.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            {filter === 'all' && 'No macro alerts configured'}
            {filter === 'subscribed' && 'No subscribed events'}
            {filter === 'unsubscribed' && 'No unsubscribed events'}
          </div>
        ) : (
          filteredSubscriptions.map((sub) => {
            const impact = sub.impact_filter || 'MEDIUM';
            return (
              <EventItem
                key={sub.event_type}
                name={eventNames[sub.event_type]}
                impactLabel={eventImpactLabels[impact]}
                impactColor={eventImpactColors[impact]}
                subscribed={sub.subscribed}
                onToggle={(checked: boolean) => handleToggle(sub.event_type, checked)}
              />
            );
          })
        )}
      </CardContent>
    </Card>
  );
};