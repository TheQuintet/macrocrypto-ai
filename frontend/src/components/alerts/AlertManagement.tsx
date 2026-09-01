import React, { useMemo, useState } from 'react';
import { usePriceAlerts } from '@/hooks/alerts/usePriceAlerts';
import { useMacroEvents } from '@/hooks/alerts/useMacroEvents';
import { PriceAlertForm } from './price/PriceAlertForm';
import { MacroAlertForm } from './macro/MacroAlertForm';
import { MacroSubscriptionFilter } from './macro/MacroSubscriptionFilter';
import { AlertListToolbar } from './shared/AlertListToolbar';
import { AlertsList } from './AlertsList';
import { AlertsEmptyState } from './AlertsEmptyState';
import { AlertDeleteConfirmation } from './AlertDeleteConfirmation';
import { AlertStatusFilter } from './AlertStatusFilter';
import { showToast } from './shared/ToastNotification';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  matchesAlertStatusFilter,
  toggledAlertStatus,
  type AlertListStatusFilter,
} from './shared/alertStatus';
import type { PriceAlert, CreatePriceAlertRequest, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert';
import type { MacroAlertDraft, MacroSubscriptionListFilter } from '@/types/alerts/macroAlert';
import type { NewAlertType } from '@/types/alerts';
import { MacroCalendarTable } from './macro/MacroCalendarTable';
import { AlertTypeSelector } from './shared/AlertTypeSelector';
import { AlertTypeSwitch } from './shared/AlertTypeSwitch';

interface AlertManagementProps {
  userId: string;
}

export const AlertManagement: React.FC<AlertManagementProps> = ({ userId }) => {
  const [creatingType, setCreatingType] = useState<NewAlertType | null>(null);
  const [showTypeSelector, setShowTypeSelector] = useState(false);
  const [editingAlert, setEditingAlert] = useState<PriceAlert | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<PriceAlert | null>(null);
  const [statusFilter, setStatusFilter] = useState<AlertListStatusFilter>('all');
  const [eventFilter, setEventFilter] = useState<MacroSubscriptionListFilter>('all');
  const [activeTab, setActiveTab] = useState<'price' | 'macro'>('price');

  const {
    alerts,
    isLoading,
    error,
    fetch: fetchAlerts,
    create: createAlert,
    update: updateAlert,
    remove: deleteAlert,
  } = usePriceAlerts(userId);

  const {
    events,
    subscriptions,
    isLoading: isLoadingEvents,
    error: eventsError,
    fetch: fetchEvents,
    subscribe: subscribeToEvent,
    applyDraft: applyMacroDraft,
  } = useMacroEvents(userId);

  const visibleAlerts = useMemo(
    () => alerts.filter((alert) => matchesAlertStatusFilter(alert.status, statusFilter)),
    [alerts, statusFilter],
  );

  const alertCounts = useMemo(
    () => ({
      all: alerts.length,
      active: alerts.filter((alert) => matchesAlertStatusFilter(alert.status, 'active')).length,
      inactive: alerts.filter((alert) => matchesAlertStatusFilter(alert.status, 'inactive'))
        .length,
    }),
    [alerts],
  );

  const eventCounts = useMemo(
    () => ({
      all: events.length,
      subscribed: events.filter((event) => event.subscribed).length,
      unsubscribed: events.filter((event) => !event.subscribed).length,
    }),
    [events],
  );

  const handleSelectAlertType = (type: NewAlertType) => {
    setActiveTab(type);
    setCreatingType(type);
  };

  const closeCreateForm = () => setCreatingType(null);

  const typeSwitcher = creatingType ? (
    <AlertTypeSwitch
      value={creatingType}
      onChange={handleSelectAlertType}
      disabled={isLoading}
    />
  ) : null;

  const handleSubscribeChange = async (eventId: string, subscribed: boolean) => {
    try {
      await subscribeToEvent(eventId, subscribed);
      showToast.success(subscribed ? 'Subscribed to event' : 'Unsubscribed from event');
    } catch {
      showToast.error('Failed to update subscription');
    }
  };

  const handleCreateMacroAlert = async (draft: MacroAlertDraft) => {
    try {
      await applyMacroDraft(draft);
      closeCreateForm();
      showToast.success('Macro event alert created');
    } catch {
      showToast.error('Failed to create alert');
    }
  };

  const handleCreate = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    try {
      await createAlert(data as CreatePriceAlertRequest);
      closeCreateForm();
      showToast.success('Alert created');
    } catch {
      showToast.error('Failed to create alert');
    }
  };

  const handleUpdate = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    if (!editingAlert) return;
    try {
      await updateAlert(editingAlert.id, data as UpdatePriceAlertRequest);
      setEditingAlert(null);
      showToast.success('Alert updated');
    } catch {
      showToast.error('Failed to update alert');
    }
  };

  const handleToggleStatus = async (alert: PriceAlert) => {
    const nextStatus = toggledAlertStatus(alert.status);
    try {
      await updateAlert(alert.id, { status: nextStatus });
      showToast.success(nextStatus === 'active' ? 'Alert activated' : 'Alert paused');
    } catch {
      showToast.error('Failed to update alert');
    }
  };

  const handleDelete = async () => {
    if (!deletingAlert) return;
    try {
      await deleteAlert(deletingAlert.id);
      setDeletingAlert(null);
      showToast.success('Alert deleted');
    } catch {
      showToast.error('Failed to delete alert');
    }
  };

  // Loading state
  if (isLoading && alerts.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <Card>
          <CardContent className="p-4">
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                  <Skeleton className="h-8 w-20" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-red-500 mb-2">Failed to load alerts</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button variant="outline" className="mt-4" onClick={fetchAlerts}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const priceAlertCount = alerts.length;

  return (
    <div className="space-y-6">
      {/* New alert + tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b">
        <Button
          size="sm"
          className="mb-2 mr-2"
          onClick={() => setShowTypeSelector(true)}
        >
          <Plus className="w-4 h-4 mr-1" />
          Create alert
        </Button>
        <button
          className={cn(
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'price'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          )}
          onClick={() => setActiveTab('price')}
        >
          Price Alerts ({priceAlertCount})
        </button>
        <button
          className={cn(
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'macro'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          )}
          onClick={() => setActiveTab('macro')}
        >
          Macro Events ({eventCounts.all})
        </button>
      </div>

      {/* Price Alerts Tab */}
      {activeTab === 'price' && (
        <>
          <AlertListToolbar
            summary={`${alerts.length} ${alerts.length === 1 ? 'alert' : 'alerts'} configured`}
          >
            <AlertStatusFilter
              value={statusFilter}
              onChange={setStatusFilter}
              counts={alertCounts}
            />
          </AlertListToolbar>

          {alerts.length === 0 ? (
            <AlertsEmptyState />
          ) : (
            <Card>
              <CardContent className="pt-4">
                <AlertsList
                  alerts={visibleAlerts}
                  onDelete={setDeletingAlert}
                  onEdit={setEditingAlert}
                  onToggleStatus={handleToggleStatus}
                />
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Macro Events Tab */}
      {activeTab === 'macro' && (
        <>
          <AlertListToolbar
            summary={`${events.length} ${events.length === 1 ? 'event' : 'events'} configured`}
          >
            <MacroSubscriptionFilter
              value={eventFilter}
              onChange={setEventFilter}
              counts={eventCounts}
            />
          </AlertListToolbar>

          <MacroCalendarTable
            events={events}
            subscriptions={subscriptions}
            isLoading={isLoadingEvents}
            error={eventsError}
            filter={eventFilter}
            onSubscribeChange={handleSubscribeChange}
            onRetry={fetchEvents}
          />
        </>
      )}

      {/* Alert Type Selection */}
      <AlertTypeSelector
        open={showTypeSelector}
        onOpenChange={setShowTypeSelector}
        onSelect={handleSelectAlertType}
      />

      {/* Create Modal */}
      <PriceAlertForm
        open={creatingType === 'price'}
        onOpenChange={(open) => (open ? setCreatingType('price') : closeCreateForm())}
        userId={userId}
        editingAlert={null}
        onSubmit={handleCreate}
        isLoading={isLoading}
        typeSwitcher={typeSwitcher}
      />

      <MacroAlertForm
        open={creatingType === 'macro'}
        onOpenChange={(open) => (open ? setCreatingType('macro') : closeCreateForm())}
        events={events}
        onSubmit={handleCreateMacroAlert}
        isLoading={isLoadingEvents}
        typeSwitcher={typeSwitcher}
      />

      {/* Edit Modal */}
      {editingAlert && (
        <PriceAlertForm
          open={!!editingAlert}
          onOpenChange={() => setEditingAlert(null)}
          userId={userId}
          editingAlert={editingAlert}
          onSubmit={handleUpdate}
          isLoading={isLoading}
        />
      )}

      {/* Delete Confirmation */}
      <AlertDeleteConfirmation
        alert={deletingAlert}
        onOpenChange={() => setDeletingAlert(null)}
        onConfirm={handleDelete}
      />
    </div>
  );
};

export default AlertManagement;