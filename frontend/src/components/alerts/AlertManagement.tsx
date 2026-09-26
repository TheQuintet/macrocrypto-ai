import React, { useMemo, useState } from 'react';
import { usePriceAlerts } from '@/hooks/alerts/usePriceAlerts';
import { useMacroEvents } from '@/hooks/alerts/useMacroEvents';
import { usePredictionAlerts } from '@/hooks/alerts/usePredictionAlerts';
import { PriceAlertForm } from './price/PriceAlertForm';
import { MacroAlertForm } from './macro/MacroAlertForm';
import { PredictionAlertForm } from './prediction/PredictionAlertForm';
import { PredictionAlertTable } from './prediction/PredictionAlertTable';
import { PredictionHistory } from './prediction/PredictionHistory';
import { PredictionAlertDeleteConfirmation } from './prediction/PredictionAlertDeleteConfirmation';
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
import { RefreshCw } from 'lucide-react';
import {
  matchesAlertStatusFilter,
  toggledAlertStatus,
  type AlertListStatusFilter,
} from './shared/alertStatus';
import type { PriceAlert, CreatePriceAlertRequest, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert';
import type {
  MacroAlertDraft,
  MacroEventStatusFilter as MacroEventStatusFilterValue,
  MacroSubscription,
} from '@/types/alerts/macroAlert';
import type { NewAlertType } from '@/types/alerts';
import type { PredictionAlert } from '@/types/alerts/predictionAlert';
import type {
  CreatePredictionAlertRequest,
  UpdatePredictionAlertRequest as UpdatePredictionAlertRequestType,
} from '@/types/alerts/predictionAlert';
import { MacroCalendarTable } from './macro/MacroCalendarTable';
import { CreateAlertButton } from './shared/CreateAlertButton';
import { AlertTypeSwitch } from './shared/AlertTypeSwitch';
import { AlertKindTabs } from './shared/AlertKindTabs';

interface AlertManagementProps {
  userId: string;
}

export const AlertManagement: React.FC<AlertManagementProps> = ({ userId }) => {
  const [creatingType, setCreatingType] = useState<NewAlertType | null>(null);
  const [editingAlert, setEditingAlert] = useState<PriceAlert | null>(null);
  const [editingSubscription, setEditingSubscription] = useState<MacroSubscription | null>(null);
  const [editingPredictionAlert, setEditingPredictionAlert] = useState<PredictionAlert | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<PriceAlert | null>(null);
  const [deletingPredictionAlert, setDeletingPredictionAlert] = useState<PredictionAlert | null>(null);
  const [statusFilter, setStatusFilter] = useState<AlertListStatusFilter>('all');
  const [eventFilter, setEventFilter] = useState<MacroEventStatusFilterValue>('all');
  const [impactFilter, setImpactFilter] = useState<ImpactFilterValue>('all');
  const [activeTab, setActiveTab] = useState<NewAlertType>('price');

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
    subscriptions,
    isLoading: isLoadingEvents,
    error: eventsError,
    fetch: fetchEvents,
    subscribe: subscribeToEvent,
    applyDraft: applyMacroDraft,
  } = useMacroEvents(userId);

  const {
    alerts: predictionAlerts,
    isLoading: isLoadingPrediction,
    error: predictionError,
    fetchAlerts: fetchPredictionAlerts,
    createAlert: createPredictionAlert,
    updateAlert: updatePredictionAlert,
    deleteAlert: deletePredictionAlert,
    toggleStatus: togglePredictionStatus,
  } = usePredictionAlerts(userId);

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
      all: subscriptions.length,
      active: subscriptions.filter((subscription) => subscription.subscribed).length,
      inactive: subscriptions.filter((subscription) => !subscription.subscribed).length,
    }),
    [subscriptions],
  );

  // Prediction alert counts
  const predictionCounts = useMemo(
    () => ({
      all: predictionAlerts.length,
      active: predictionAlerts.filter((a) => a.status === 'active' || a.status === 'triggered').length,
      inactive: predictionAlerts.filter((a) => a.status === 'disabled' || a.status === 'expired').length,
    }),
    [predictionAlerts],
  );

  const visiblePredictionAlerts = useMemo(
    () => predictionAlerts.filter((alert) => {
      if (statusFilter === 'all') return true;
      const isActive = alert.status === 'active' || alert.status === 'triggered';
      return statusFilter === 'active' ? isActive : !isActive;
    }),
    [predictionAlerts, statusFilter],
  );

  // Handle all three alert types correctly
  const handleSelectAlertType = (type: NewAlertType) => {
    // Set the active tab based on the selected type
    if (type === 'price') {
      setActiveTab('price');
    } else if (type === 'macro') {
      setActiveTab('macro');
    } else if (type === 'prediction') {
      setActiveTab('prediction');
    }
    // Set the creating type to open the right form
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

  const editingEventDraft: MacroAlertDraft | null = editingSubscription
    ? {
        event_type: editingSubscription.event_type,
        timing: editingSubscription.timing ?? '1D',
        one_time: editingSubscription.one_time ?? true,
        notify_in_app: editingSubscription.notify_in_app ?? true,
        notify_email: editingSubscription.notify_email ?? false,
      }
    : null;

  const macroFormKey = editingSubscription
    ? `macro-edit-${editingSubscription.event_type}`
    : 'macro-create';

  const handleSubmitMacroAlert = async (draft: MacroAlertDraft) => {
    const wasEditing = Boolean(editingSubscription);
    try {
      await applyMacroDraft(draft);
      closeCreateForm();
      setEditingSubscription(null);
      showToast.success(wasEditing ? 'Alert updated' : 'Macro event alert created');
    } catch {
      showToast.error(wasEditing ? 'Failed to update alert' : 'Failed to create alert');
    }
  };

  const handleCreatePriceAlert = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    try {
      await createAlert(data as CreatePriceAlertRequest);
      closeCreateForm();
      showToast.success('Alert created');
    } catch {
      showToast.error('Failed to create alert');
    }
  };

  const handleUpdatePriceAlert = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    if (!editingAlert) return;
    try {
      await updateAlert(editingAlert.id, data as UpdatePriceAlertRequest);
      setEditingAlert(null);
      showToast.success('Alert updated');
    } catch {
      showToast.error('Failed to update alert');
    }
  };

  const handleTogglePriceStatus = async (alert: PriceAlert) => {
    const nextStatus = toggledAlertStatus(alert.status);
    try {
      await updateAlert(alert.id, { status: nextStatus });
      showToast.success(nextStatus === 'active' ? 'Alert activated' : 'Alert paused');
    } catch {
      showToast.error('Failed to update alert');
    }
  };

  const handleDeletePriceAlert = async () => {
    if (!deletingAlert) return;
    try {
      await deleteAlert(deletingAlert.id);
      setDeletingAlert(null);
      showToast.success('Alert deleted');
    } catch {
      showToast.error('Failed to delete alert');
    }
  };

  // Prediction alert handlers
  const handleCreatePredictionAlert = async (
    data: CreatePredictionAlertRequest | UpdatePredictionAlertRequestType
  ) => {
    try {
      // Ensure we have user_id for create
      const createData = data as CreatePredictionAlertRequest;
      await createPredictionAlert({ ...createData, user_id: userId });
      setCreatingType(null);
      showToast.success('Prediction alert created');
    } catch {
      showToast.error('Failed to create prediction alert');
    }
  };

  const handleUpdatePredictionAlert = async (data: UpdatePredictionAlertRequestType) => {
    if (!editingPredictionAlert) return;
    try {
      await updatePredictionAlert(editingPredictionAlert.id, data);
      setEditingPredictionAlert(null);
      showToast.success('Prediction alert updated');
    } catch {
      showToast.error('Failed to update prediction alert');
    }
  };

  const handleDeletePredictionAlert = async () => {
    if (!deletingPredictionAlert) return;
    try {
      await deletePredictionAlert(deletingPredictionAlert.id);
      setDeletingPredictionAlert(null);
      showToast.success('Prediction alert deleted');
    } catch {
      showToast.error('Failed to delete prediction alert');
    }
  };

  const handleTogglePredictionStatus = async (alert: PredictionAlert) => {
    try {
      await togglePredictionStatus(alert.id);
      showToast.success(
        alert.status === 'active' || alert.status === 'triggered'
          ? 'Alert paused'
          : 'Alert activated'
      );
    } catch {
      showToast.error('Failed to update alert');
    }
  };

  // Loading state
  const isAnyLoading = isLoading || isLoadingEvents || isLoadingPrediction;
  if (
    isAnyLoading
    && alerts.length === 0
    && subscriptions.length === 0
    && predictionAlerts.length === 0
  ) {
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
  if (error || eventsError || predictionError) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-red-500 mb-2">Failed to load alerts</p>
          <p className="text-sm text-muted-foreground">{error || eventsError || predictionError}</p>
          <Button variant="outline" className="mt-4" onClick={() => {
            fetchAlerts();
            fetchEvents();
            fetchPredictionAlerts();
          }}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const priceAlertCount = alerts.length;
  const macroEventCount = subscriptions.length;
  const predictionCount = predictionAlerts.length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2 border-b">
        <AlertKindTabs
          value={activeTab}
          onChange={setActiveTab}
          counts={{
            price: priceAlertCount,
            macro: macroEventCount,
            prediction: predictionCount,
          }}
        />
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
            <CreateAlertButton kind="price" onClick={() => setCreatingType('price')} />
          </AlertListToolbar>

          {alerts.length === 0 ? (
            <AlertsEmptyState />
          ) : (
            <PriceAlertTable
              alerts={visibleAlerts}
              onDelete={setDeletingAlert}
              onEdit={setEditingAlert}
              onToggleStatus={handleTogglePriceStatus}
            />
          )}
        </>
      )}

      {/* Macro Events Tab */}
      {activeTab === 'macro' && (
        <>
          <AlertListToolbar
            summary={`${subscriptions.length} event ${subscriptions.length === 1 ? 'type' : 'types'}`}
          >
            <MacroEventStatusFilter
              value={eventFilter}
              onChange={setEventFilter}
              counts={eventCounts}
            />
            <MacroImpactFilter value={impactFilter} onChange={setImpactFilter} />
            <CreateAlertButton kind="macro" onClick={() => setCreatingType('macro')} />
          </AlertListToolbar>

          <MacroCalendarTable
            subscriptions={subscriptions}
            isLoading={isLoadingEvents}
            error={eventsError}
            filter={eventFilter}
            impactFilter={impactFilter}
            onSubscribeChange={handleSubscribeChange}
            onDelete={handleDeleteMacroAlert}
            onEdit={setEditingSubscription}
            onRetry={fetchEvents}
          />
        </>
      )}

      {/* Prediction Alerts Tab */}
      {activeTab === 'prediction' && (
        <div className="space-y-6">
          <AlertListToolbar
            summary={`${predictionAlerts.length} ${predictionAlerts.length === 1 ? 'alert' : 'alerts'} configured`}
          >
            <AlertStatusFilter
              value={statusFilter}
              onChange={setStatusFilter}
              counts={predictionCounts}
            />
            <CreateAlertButton
              kind="prediction"
              onClick={() => setCreatingType('prediction')}
            />
          </AlertListToolbar>

          {predictionAlerts.length === 0 ? (
            <AlertsEmptyState />
          ) : (
            <PredictionAlertTable
              alerts={visiblePredictionAlerts}
              onDelete={setDeletingPredictionAlert}
              onEdit={setEditingPredictionAlert}
              onToggleStatus={handleTogglePredictionStatus}
            />
          )}

          {/* History section */}
          <div className="pt-4 border-t">
            <PredictionHistory userId={userId} />
          </div>
        </div>
      )}

      {/* Create Price Alert Modal - only show when price is selected */}
      {creatingType === 'price' && (
        <PriceAlertForm
          open={creatingType === 'price'}
          onOpenChange={(open) => (open ? setCreatingType('price') : closeCreateForm())}
          userId={userId}
          editingAlert={null}
          onSubmit={handleCreatePriceAlert}
          isLoading={isLoading}
          typeSwitcher={typeSwitcher}
        />
      )}

      {/* Create Macro Alert Modal - only show when macro is selected */}
      {creatingType === 'macro' && (
        <MacroAlertForm
          key={macroFormKey}
          open={creatingType === 'macro' || Boolean(editingSubscription)}
          onOpenChange={(open) => {
            if (open) return;
            closeCreateForm();
            setEditingSubscription(null);
          }}
          editingDraft={editingEventDraft}
          onSubmit={handleSubmitMacroAlert}
          isLoading={isLoadingEvents}
          typeSwitcher={typeSwitcher}
        />
      )}

      {/* Edit Macro Alert Modal */}
      {editingSubscription && creatingType !== 'macro' && (
        <MacroAlertForm
          key={macroFormKey}
          open
          onOpenChange={(open) => {
            if (!open) setEditingSubscription(null);
          }}
          editingDraft={editingEventDraft}
          onSubmit={handleSubmitMacroAlert}
          isLoading={isLoadingEvents}
        />
      )}

      {/* Create Prediction Alert Modal - only show when prediction is selected */}
      {creatingType === 'prediction' && (
        <PredictionAlertForm
          open={creatingType === 'prediction'}
          onOpenChange={(open) => (open ? setCreatingType('prediction') : closeCreateForm())}
          userId={userId}
          editingAlert={null}
          onSubmit={handleCreatePredictionAlert}
          isLoading={isLoadingPrediction}
          typeSwitcher={typeSwitcher}
        />
      )}

      {/* Edit Price Alert Modal */}
      {editingAlert && (
        <PriceAlertForm
          open={!!editingAlert}
          onOpenChange={() => setEditingAlert(null)}
          userId={userId}
          editingAlert={editingAlert}
          onSubmit={handleUpdatePriceAlert}
          isLoading={isLoading}
        />
      )}

      {/* Edit Prediction Alert Modal */}
      {editingPredictionAlert && (
        <PredictionAlertForm
          open={!!editingPredictionAlert}
          onOpenChange={() => setEditingPredictionAlert(null)}
          userId={userId}
          editingAlert={editingPredictionAlert}
          onSubmit={handleUpdatePredictionAlert}
          isLoading={isLoadingPrediction}
        />
      )}

      {/* Delete Confirmation for Price Alerts */}
      <AlertDeleteConfirmation
        alert={deletingAlert}
        onOpenChange={() => setDeletingAlert(null)}
        onConfirm={handleDeletePriceAlert}
      />

      <PredictionAlertDeleteConfirmation
        alert={deletingPredictionAlert}
        onOpenChange={() => setDeletingPredictionAlert(null)}
        onConfirm={handleDeletePredictionAlert}
        isLoading={isLoadingPrediction}
      />
    </div>
  );
};

export default AlertManagement;