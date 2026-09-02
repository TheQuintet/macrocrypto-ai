import React, { useMemo, useState } from 'react';
import { usePriceAlerts } from '@/hooks/alerts/usePriceAlerts';
import { useMacroEvents } from '@/hooks/alerts/useMacroEvents';
import { PriceAlertForm } from './price/PriceAlertForm';
import { MacroAlertForm } from './macro/MacroAlertForm';
import { MacroEventStatusFilter } from './macro/MacroEventStatusFilter';
import { MacroImpactFilter, type ImpactFilterValue } from './macro/MacroImpactFilter';
import { AlertListToolbar } from './shared/AlertListToolbar';
import { PriceAlertTable } from './price/PriceAlertTable';
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
import type {
  MacroAlertDraft,
  MacroEvent,
  MacroEventStatusFilter as MacroEventStatusFilterValue,
} from '@/types/alerts/macroAlert';
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
  const [editingEvent, setEditingEvent] = useState<MacroEvent | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<PriceAlert | null>(null);
  const [statusFilter, setStatusFilter] = useState<AlertListStatusFilter>('all');
  const [eventFilter, setEventFilter] = useState<MacroEventStatusFilterValue>('all');
  const [impactFilter, setImpactFilter] = useState<ImpactFilterValue>('all');
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
      active: events.filter((event) => event.subscribed).length,
      inactive: events.filter((event) => !event.subscribed).length,
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
      showToast.success(subscribed ? 'Alert activated' : 'Alert paused');
    } catch {
      showToast.error('Failed to update subscription');
    }
  };

  const handleDeleteMacroAlert = async (eventId: string) => {
    try {
      await subscribeToEvent(eventId, false);
      showToast.success('Alert deleted');
    } catch {
      showToast.error('Failed to delete alert');
    }
  };

  const editingEventDraft: MacroAlertDraft | null = editingEvent
    ? {
        event_type: editingEvent.event_type,
        timing: subscriptions.get(editingEvent.event_type)?.timing ?? '1D',
        one_time: subscriptions.get(editingEvent.event_type)?.oneTime ?? true,
        notify_in_app: true,
        notify_email: false,
      }
    : null;

  const handleSubmitMacroAlert = async (draft: MacroAlertDraft) => {
    const wasEditing = Boolean(editingEvent);
    try {
      await applyMacroDraft(draft);
      closeCreateForm();
      setEditingEvent(null);
      showToast.success(wasEditing ? 'Alert updated' : 'Macro event alert created');
    } catch {
      showToast.error(wasEditing ? 'Failed to update alert' : 'Failed to create alert');
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
            <PriceAlertTable
              alerts={visibleAlerts}
              onDelete={setDeletingAlert}
              onEdit={setEditingAlert}
              onToggleStatus={handleToggleStatus}
            />
          )}
        </>
      )}

      {/* Macro Events Tab */}
      {activeTab === 'macro' && (
        <>
          <AlertListToolbar
            summary={`${events.length} ${events.length === 1 ? 'event' : 'events'} configured`}
          >
            <MacroEventStatusFilter
              value={eventFilter}
              onChange={setEventFilter}
              counts={eventCounts}
            />
            <MacroImpactFilter value={impactFilter} onChange={setImpactFilter} />
          </AlertListToolbar>

          <MacroCalendarTable
            events={events}
            subscriptions={subscriptions}
            isLoading={isLoadingEvents}
            error={eventsError}
            filter={eventFilter}
            impactFilter={impactFilter}
            onSubscribeChange={handleSubscribeChange}
            onDelete={handleDeleteMacroAlert}
            onEdit={setEditingEvent}
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
        open={creatingType === 'macro' || Boolean(editingEvent)}
        onOpenChange={(open) => {
          if (open) return;
          closeCreateForm();
          setEditingEvent(null);
        }}
        events={events}
        editingDraft={editingEventDraft}
        onSubmit={handleSubmitMacroAlert}
        isLoading={isLoadingEvents}
        typeSwitcher={editingEvent ? undefined : typeSwitcher}
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