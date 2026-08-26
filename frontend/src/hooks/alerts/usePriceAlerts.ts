import { useEffect, useCallback } from 'react';
import { usePriceAlertStore } from '@/stores/alerts/priceAlertStore';
import type { CreatePriceAlertRequest, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert';

interface UsePriceAlertsOptions {
  autoFetch?: boolean;
  filters?: { status?: string; alert_type?: string };
}

export const usePriceAlerts = (userId: string, options: UsePriceAlertsOptions = {}) => {
  const { autoFetch = true, filters } = options;
  const {
    alerts,
    isLoading,
    error,
    fetchAlerts,
    createAlert,
    updateAlert,
    deleteAlert,
    triggerAlert,
    clearError,
  } = usePriceAlertStore();

  const fetch = useCallback(() => {
    if (userId) {
      fetchAlerts(userId, filters);
    }
  }, [userId, filters, fetchAlerts]);

  const create = useCallback(
    async (data: CreatePriceAlertRequest) => {
      return createAlert({ ...data, user_id: userId });
    },
    [userId, createAlert]
  );

  const update = useCallback(
    async (id: string, data: UpdatePriceAlertRequest) => {
      return updateAlert(id, data);
    },
    [updateAlert]
  );

  const remove = useCallback(
    async (id: string) => {
      return deleteAlert(id);
    },
    [deleteAlert]
  );

  const trigger = useCallback(
    async (id: string) => {
      return triggerAlert(id);
    },
    [triggerAlert]
  );

  useEffect(() => {
    if (autoFetch && userId) {
      fetch();
    }
  }, [autoFetch, userId, fetch]);

  return {
    alerts,
    isLoading,
    error,
    fetch,
    create,
    update,
    remove,
    trigger,
    clearError,
  };
};