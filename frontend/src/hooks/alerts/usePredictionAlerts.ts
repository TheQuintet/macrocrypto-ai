// frontend/src/hooks/alerts/usePredictionAlerts.ts

import { useState, useEffect, useCallback } from 'react';
import { predictionAlertApi } from '@/api/alerts/predictionAlerts';
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert';

export function usePredictionAlerts(userId: string) {
  const [alerts, setAlerts] = useState<PredictionAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await predictionAlertApi.getAlerts(userId);
      setAlerts(data);
    } catch (err) {
      setError('Failed to load prediction alerts');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const createAlert = useCallback(async (data: CreatePredictionAlertRequest) => {
    const newAlert = await predictionAlertApi.createAlert(data);
    setAlerts((prev) => [...prev, newAlert]);
    return newAlert;
  }, []);

  const updateAlert = useCallback(
    async (alertId: string, data: UpdatePredictionAlertRequest) => {
      const updated = await predictionAlertApi.updateAlert(alertId, data);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
      return updated;
    },
    [],
  );

  const deleteAlert = useCallback(async (alertId: string) => {
    await predictionAlertApi.deleteAlert(alertId);
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  }, []);

  const toggleStatus = useCallback(async (alertId: string) => {
    const updated = await predictionAlertApi.toggleStatus(alertId);
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
    return updated;
  }, []);

  // Fixed: Load alerts in a separate async function
  useEffect(() => {
    const loadAlerts = async () => {
      if (userId) {
        setIsLoading(true);
        setError(null);
        try {
          const data = await predictionAlertApi.getAlerts(userId);
          setAlerts(data);
        } catch (err) {
          setError('Failed to load prediction alerts');
          console.error(err);
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadAlerts();
  }, [userId]);

  return {
    alerts,
    isLoading,
    error,
    fetchAlerts,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleStatus,
  };
}