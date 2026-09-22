import { useCallback, useEffect, useState } from 'react'
import { predictionAlertApi } from '@/api/alerts/predictionAlerts'
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert'

export function usePredictionAlerts(userId: string) {
  const [alerts, setAlerts] = useState<PredictionAlert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAlerts = useCallback(async () => {
    if (!userId) return
    setIsLoading(true)
    setError(null)
    try {
      setAlerts(await predictionAlertApi.getAlerts(userId))
    } catch (err) {
      setError('Failed to load prediction alerts')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const createAlert = useCallback(async (data: CreatePredictionAlertRequest) => {
    const newAlert = await predictionAlertApi.createAlert(data)
    setAlerts((prev) => [...prev, newAlert])
    return newAlert
  }, [])

  const updateAlert = useCallback(
    async (alertId: string, data: UpdatePredictionAlertRequest) => {
      const updated = await predictionAlertApi.updateAlert(alertId, data)
      setAlerts((prev) => prev.map((alert) => (alert.id === alertId ? updated : alert)))
      return updated
    },
    [],
  )

  const deleteAlert = useCallback(async (alertId: string) => {
    await predictionAlertApi.deleteAlert(alertId)
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId))
  }, [])

  const toggleStatus = useCallback(async (alertId: string) => {
    const updated = await predictionAlertApi.toggleStatus(alertId)
    setAlerts((prev) => prev.map((alert) => (alert.id === alertId ? updated : alert)))
    return updated
  }, [])

  useEffect(() => {
    let active = true

    const loadAlerts = async () => {
      if (!userId) return
      try {
        const data = await predictionAlertApi.getAlerts(userId)
        if (!active) return
        setAlerts(data)
        setError(null)
      } catch (err) {
        if (!active) return
        setError('Failed to load prediction alerts')
        console.error(err)
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void loadAlerts()
    return () => {
      active = false
    }
  }, [userId])

  return {
    alerts,
    isLoading,
    error,
    fetchAlerts,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleStatus,
  }
}
