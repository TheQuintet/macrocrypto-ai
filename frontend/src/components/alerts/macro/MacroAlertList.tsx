import React, { useState, useEffect, useMemo } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { showToast } from '../shared/ToastNotification';
import { ConfirmationDialog } from '../shared/ConfirmationDialog';
import { AlertCircle, RefreshCw, Trash2, Bell, BellOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MacroSubscription, EventType } from '@/types/alerts/macroAlert';
import { macroAlertApi } from '@/api/alerts/macroAlerts';

type FilterType = 'all' | 'subscribed' | 'unsubscribed';
type ImpactLevel = 'HIGH' | 'MEDIUM' | 'LOW';

const timingOptions = [
  { value: '1D', label: '1 day' },
  { value: '12H', label: '12 hours' },
  { value: '1H', label: '1 hour' },
];

const EventItem = ({
  name,
  impactLabel,
  impactColor,
  eventColor,
  icon,
  subscribed,
  timing,
  onToggle,
  onTimingChange,
  onDelete,
  disabled = false,
}: {
  name: string;
  impactLabel: string;
  impactColor: string;
  eventColor: string;
  icon: string;
  subscribed: boolean;
  timing: string;
  onToggle: (checked: boolean) => void;
  onTimingChange: (value: string) => void;
  onDelete: () => void;
  disabled?: boolean;
}) => {
  return (
    <div
      className={cn(
        'group flex flex-col md:flex-row md:items-center gap-3 p-4 rounded-xl border transition-all duration-200',
        subscribed 
          ? 'border-primary/20 bg-primary/5 hover:border-primary/40' 
          : 'border-border bg-card hover:border-muted-foreground/20',
        eventColor
      )}
    >
      <div className="flex items-center gap-3 min-w-[180px] flex-1 md:flex-none">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted/50 text-xl shrink-0">
          {icon}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm truncate">{name}</span>
            <Badge variant="outline" className={cn('text-xs shrink-0', impactColor)}>
              {impactLabel}
            </Badge>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            {subscribed ? (
              <Bell className="h-3 w-3 text-primary" />
            ) : (
              <BellOff className="h-3 w-3 text-muted-foreground" />
            )}
            <span className="text-xs text-muted-foreground">
              {subscribed ? 'Active' : 'Paused'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 flex-1">
        <div className="flex items-center gap-2">
          <Switch
            checked={subscribed}
            onCheckedChange={onToggle}
            disabled={disabled}
            className="data-[state=checked]:bg-primary"
          />
          <span className="text-xs text-muted-foreground min-w-[70px]">
            {subscribed ? 'On' : 'Off'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Notify:</span>
          <select
            value={timing}
            onChange={(e) => onTimingChange(e.target.value)}
            disabled={!subscribed || disabled}
            className={cn(
              'h-8 px-2.5 text-xs rounded-lg border bg-background transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-primary/20',
              !subscribed && 'opacity-50 cursor-not-allowed'
            )}
          >
            {timingOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center justify-end md:ml-auto shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-50 transition-colors"
          onClick={onDelete}
          disabled={disabled}
          aria-label={`Unsubscribe from ${name}`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

// Impact Filter Component
const ImpactFilter = ({
  selected,
  onChange,
}: {
  selected: ImpactLevel[];
  onChange: (levels: ImpactLevel[]) => void;
}) => {
  const impactOptions: { value: ImpactLevel; label: string; color: string }[] = [
    { value: 'HIGH', label: 'High Impact', color: 'text-red-500 border-red-200 bg-red-50 dark:bg-red-950/20' },
    { value: 'MEDIUM', label: 'Medium Impact', color: 'text-yellow-500 border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20' },
    { value: 'LOW', label: 'Low Impact', color: 'text-green-500 border-green-200 bg-green-50 dark:bg-green-950/20' },
  ];

  const isAllSelected = selected.length === 3;
  const isNoneSelected = selected.length === 0;

  const handleAllToggle = () => {
    if (isAllSelected) {
      onChange([]);
    } else {
      onChange(['HIGH', 'MEDIUM', 'LOW']);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-muted-foreground mr-1">Impact:</span>
      <button
        onClick={handleAllToggle}
        className={cn(
          'px-2 py-0.5 text-xs rounded-md border transition-colors',
          isAllSelected
            ? 'bg-primary text-primary-foreground border-primary'
            : 'border-border hover:bg-muted'
        )}
      >
        {isAllSelected ? 'All ✓' : 'All'}
      </button>
      {impactOptions.map((option) => {
        const isSelected = selected.includes(option.value);
        return (
          <button
            key={option.value}
            onClick={() => {
              if (isSelected) {
                onChange(selected.filter((i) => i !== option.value));
              } else {
                onChange([...selected, option.value]);
              }
            }}
            className={cn(
              'px-2 py-0.5 text-xs rounded-md border transition-colors',
              option.color,
              isSelected
                ? 'ring-1 ring-primary/50'
                : 'opacity-50 hover:opacity-100'
            )}
          >
            {option.label}
            {isSelected ? ' ✓' : ''}
          </button>
        );
      })}
      {isNoneSelected && (
        <span className="text-xs text-muted-foreground ml-1">(showing all)</span>
      )}
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
  const [impactFilter, setImpactFilter] = useState<ImpactLevel[]>(['HIGH', 'MEDIUM']);
  const [deletingEvent, setDeletingEvent] = useState<{ eventType: EventType; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const eventNames: Record<EventType, string> = {
    FED: 'Federal Reserve',
    CPI: 'Consumer Price Index',
    GDP: 'Gross Domestic Product',
    EMPLOYMENT: 'Employment Report',
  };

  const eventImpactLabels: Record<string, string> = {
    HIGH: 'High Impact',
    MEDIUM: 'Medium Impact',
    LOW: 'Low Impact',
  };

  const eventImpactColors: Record<string, string> = {
    HIGH: 'text-red-500 border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800',
    MEDIUM: 'text-yellow-500 border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20 dark:border-yellow-800',
    LOW: 'text-green-500 border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800',
  };

  const eventColors: Record<string, string> = {
    FED: 'dark:border-purple-800',
    CPI: 'dark:border-blue-800',
    GDP: 'dark:border-green-800',
    EMPLOYMENT: 'dark:border-orange-800',
  };

  const eventIcons: Record<string, string> = {
    FED: '🏛️',
    CPI: '📊',
    GDP: '📈',
    EMPLOYMENT: '👔',
  };

  const filteredSubscriptions = useMemo(() => {
    let result = subscriptions;

    if (filter === 'subscribed') {
      result = result.filter((s) => s.subscribed);
    } else if (filter === 'unsubscribed') {
      result = result.filter((s) => !s.subscribed);
    }

    if (impactFilter.length > 0 && impactFilter.length < 3) {
      result = result.filter((s) => {
        const impact = s.impact_filter || 'MEDIUM';
        return impactFilter.includes(impact as ImpactLevel);
      });
    }

    return result;
  }, [subscriptions, filter, impactFilter]);

  useEffect(() => {
    const loadSubscriptions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await macroAlertApi.getSubscriptions(userId);
        setSubscriptions(data);
      } catch {
        console.error('[MacroAlertList] Error');
        setError('Failed to load subscriptions');
      } finally {
        setIsLoading(false);
      }
    };

    loadSubscriptions();
  }, [userId]);

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

  const handleTimingChange = async (eventType: EventType, timing: string) => {
    try {
      setSubscriptions((prev) =>
        prev.map((s) =>
          s.event_type === eventType ? { ...s, timing: timing as '1D' | '12H' | '1H' } : s
        )
      );
      showToast.success(`Timing updated for ${eventType}`);
    } catch {
      showToast.error('Failed to update timing');
    }
  };

  const handleDelete = async () => {
    if (!deletingEvent) return;
    setIsDeleting(true);
    try {
      await macroAlertApi.updateSubscription(userId, deletingEvent.eventType, false);
      setSubscriptions((prev) =>
        prev.map((s) =>
          s.event_type === deletingEvent.eventType
            ? { ...s, subscribed: false }
            : s
        )
      );
      setDeletingEvent(null);
      showToast.success(`${deletingEvent.name} unsubscribed`);
    } catch {
      showToast.error('Failed to unsubscribe');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setError(null);
    macroAlertApi.getSubscriptions(userId)
      .then((data: MacroSubscription[]) => {
        setSubscriptions(data);
        showToast.info('Refreshed');
      })
      .catch(() => {
        setError('Failed to load subscriptions');
        showToast.error('Failed to refresh');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const getFilterCount = (type: FilterType) => {
    if (type === 'all') return subscriptions.length;
    if (type === 'subscribed') return subscriptions.filter((s) => s.subscribed).length;
    return subscriptions.filter((s) => !s.subscribed).length;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Macro Alerts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
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
    <>
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <CardTitle>Macro Alerts</CardTitle>
            <Badge variant="secondary" className="text-xs">
              {subscriptions.length}
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
                All ({getFilterCount('all')})
              </Button>
              <Button
                variant={filter === 'subscribed' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('subscribed')}
                className="h-7 text-xs text-green-600"
              >
                On ({getFilterCount('subscribed')})
              </Button>
              <Button
                variant={filter === 'unsubscribed' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('unsubscribed')}
                className="h-7 text-xs text-muted-foreground"
              >
                Off ({getFilterCount('unsubscribed')})
              </Button>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              className="h-7 w-7 p-0"
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
          </div>
        </CardHeader>

        <div className="px-6 pb-2">
          <ImpactFilter
            selected={impactFilter}
            onChange={setImpactFilter}
          />
        </div>

        <CardContent className="space-y-2 pt-0">
          {filteredSubscriptions.length === 0 ? (
            <div className="py-12 text-center">
              <BellOff className="h-12 w-12 mx-auto text-muted-foreground/50" />
              <p className="mt-3 text-muted-foreground">
                {filter === 'all' && 'No macro alerts match your filters'}
                {filter === 'subscribed' && 'No subscribed events'}
                {filter === 'unsubscribed' && 'No unsubscribed events'}
              </p>
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
                  eventColor={eventColors[sub.event_type] || ''}
                  icon={eventIcons[sub.event_type] || '📋'}
                  subscribed={sub.subscribed}
                  timing={sub.timing || '1D'}
                  onToggle={(checked) => handleToggle(sub.event_type, checked)}
                  onTimingChange={(value) => handleTimingChange(sub.event_type, value)}
                  onDelete={() => setDeletingEvent({ 
                    eventType: sub.event_type, 
                    name: eventNames[sub.event_type] 
                  })}
                />
              );
            })
          )}
        </CardContent>
      </Card>

      <ConfirmationDialog
        open={!!deletingEvent}
        onOpenChange={() => setDeletingEvent(null)}
        onConfirm={handleDelete}
        title="Unsubscribe from Event"
        description={`Are you sure you want to unsubscribe from "${deletingEvent?.name}"? You will no longer receive reminders for this event.`}
        confirmText="Unsubscribe"
        variant="destructive"
        isLoading={isDeleting}
      />
    </>
  );
};