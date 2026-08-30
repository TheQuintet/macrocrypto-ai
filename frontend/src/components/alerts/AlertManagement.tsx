import React, { useMemo, useState } from 'react';
import { usePriceAlerts } from '@/hooks/alerts/usePriceAlerts';
import { PriceAlertForm } from './price/PriceAlertForm';
import { AlertsList } from './AlertsList';
import { AlertsEmptyState } from './AlertsEmptyState';
import { AlertStatusFilter } from './AlertStatusFilter';
import { ConfirmationDialog } from './shared/ConfirmationDialog';
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

interface AlertManagementProps {
  userId: string;
}

export const AlertManagement: React.FC<AlertManagementProps> = ({ userId }) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState<PriceAlert | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<PriceAlert | null>(null);
  const [statusFilter, setStatusFilter] = useState<AlertListStatusFilter>('all');

  const {
    alerts,
    isLoading,
    error,
    fetch: fetchAlerts,
    create: createAlert,
    update: updateAlert,
    remove: deleteAlert,
  } = usePriceAlerts(userId);

  const visibleAlerts = useMemo(
    () => alerts.filter((alert) => matchesAlertStatusFilter(alert.status, statusFilter)),
    [alerts, statusFilter],
  );

  const handleRefresh = () => {
    fetchAlerts();
    showToast.info('Refreshing alerts...');
  };

  const handleCreate = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    try {
      await createAlert(data as CreatePriceAlertRequest);
      setShowCreateModal(false);
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
          <Button variant="outline" className="mt-4" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {alerts.length > 0 ? (
          <AlertStatusFilter value={statusFilter} onChange={setStatusFilter} />
        ) : null}
        <div className="flex items-center gap-2 sm:ml-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={cn('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Alert
          </Button>
        </div>
      </div>

      {/* Alert List */}
      {alerts.length === 0 ? (
        <AlertsEmptyState onCreateAlert={() => setShowCreateModal(true)} />
      ) : visibleAlerts.length === 0 ? (
        <p className="p-8 text-center text-muted-foreground">
          {statusFilter === 'active' ? 'No active alerts' : 'No inactive alerts'}
        </p>
      ) : (
        <AlertsList
          alerts={visibleAlerts}
          onDelete={setDeletingAlert}
          onEdit={setEditingAlert}
          onToggleStatus={handleToggleStatus}
        />
      )}

      {/* Create Modal */}
      <PriceAlertForm
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        userId={userId}
        editingAlert={null}
        onSubmit={handleCreate}
        isLoading={isLoading}
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
      <ConfirmationDialog
        open={!!deletingAlert}
        onOpenChange={() => setDeletingAlert(null)}
        onConfirm={handleDelete}
        title="Delete alert"
        description={`Delete "${deletingAlert?.name || 'this alert'}"?`}
        confirmText="Delete"
        variant="destructive"
      />
    </div>
  );
};