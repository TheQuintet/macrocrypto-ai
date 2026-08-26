import React, { useState } from 'react';
import { usePriceAlerts } from '@/hooks/alerts/usePriceAlerts';
import { PriceAlertForm } from './price/PriceAlertForm';
import { AlertsList } from './AlertsList';
import { AlertsEmptyState } from './AlertsEmptyState';
import { ConfirmationDialog } from './shared/ConfirmationDialog';
import { showToast } from './shared/ToastNotification';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PriceAlert, CreatePriceAlertRequest, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert';

interface AlertManagementProps {
  userId: string;
}

export const AlertManagement: React.FC<AlertManagementProps> = ({ userId }) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState<PriceAlert | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<PriceAlert | null>(null);

  const {
    alerts,
    isLoading,
    error,
    fetch: fetchAlerts,
    create: createAlert,
    update: updateAlert,
    remove: deleteAlert,
  } = usePriceAlerts(userId);

  const handleRefresh = () => {
    fetchAlerts();
    showToast.info('Refreshing alerts...');
  };

  const handleCreate = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    try {
      await createAlert(data as CreatePriceAlertRequest);
      setShowCreateModal(false);
      showToast.success('Alert created successfully');
    } catch {
      showToast.error('Failed to create alert');
    }
  };

  const handleUpdate = async (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => {
    if (!editingAlert) return;
    try {
      await updateAlert(editingAlert.id, data as UpdatePriceAlertRequest);
      setEditingAlert(null);
      showToast.success('Alert updated successfully');
    } catch {
      showToast.error('Failed to update alert');
    }
  };

  const handleDelete = async () => {
    if (!deletingAlert) return;
    try {
      await deleteAlert(deletingAlert.id);
      setDeletingAlert(null);
      showToast.success('Alert deleted successfully');
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Price Alerts</h2>
          <p className="text-sm text-muted-foreground">
            {alerts.length} {alerts.length === 1 ? 'alert' : 'alerts'} configured
          </p>
        </div>
        <div className="flex items-center gap-2">
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
      ) : (
        <Card>
          <CardHeader className="pb-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Your Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <AlertsList
              alerts={alerts}
              onDelete={setDeletingAlert}
              onEdit={setEditingAlert}
            />
          </CardContent>
        </Card>
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
        title="Delete Alert"
        description={`Are you sure you want to delete the alert "${deletingAlert?.name || 'Untitled'}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="destructive"
      />
    </div>
  );
};