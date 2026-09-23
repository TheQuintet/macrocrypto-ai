import axios from 'axios'
import { PREDICTION_ALERTS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import {
  toCreateApiPayload,
  toUiAlert,
  toUpdateApiPayload,
} from '@/lib/alerts/predictionAlertMapping'
import {
  simulateCreateAlert,
  simulateDeleteAlert,
  simulateExportHistory,
  simulateGetAlerts,
  simulateGetHistory,
  simulateToggleStatus,
  simulateUpdateAlert,
  type HistoryQuery,
} from './simulatedPredictionAlerts'
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  PredictionAlertApiRecord,
  PredictionAlertListResponse,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert'

const JSON_HEADERS = { Accept: 'application/json' }

/**
 * Prediction-alert CRUD from the alert service.
 *
 * Gateway set → live HTTP. Unset → simulated seed data. Failed live
 * requests throw; they do not fall back.
 *
 * History and CSV export have no backend routes yet, so those stay simulated
 * (or empty when live) until the service adds them.
 */
async function fromApiOrSimulate<T>(
  path: string,
  simulate: () => Promise<T>,
  live: (url: string) => Promise<T>,
): Promise<T> {
  const url = apiUrl(path)
  if (!url) {
    return simulate()
  }

  return live(url)
}

function itemPath(alertId: string) {
  return `${PREDICTION_ALERTS_PATH}${alertId}`
}

function mapList(payload: PredictionAlertListResponse | PredictionAlertApiRecord[]) {
  const rows = Array.isArray(payload) ? payload : (payload.alerts ?? [])
  return rows
    .map((row) => toUiAlert(row))
    .filter((row): row is PredictionAlert => row !== null)
}

function requireUiAlert(row: PredictionAlertApiRecord): PredictionAlert {
  const alert = toUiAlert(row)
  if (!alert) {
    throw new Error('Prediction alert response is missing id or user_id')
  }
  return alert
}

export const predictionAlertApi = {
  getAlerts: async (userId: string): Promise<PredictionAlert[]> =>
    fromApiOrSimulate(
      PREDICTION_ALERTS_PATH,
      () => simulateGetAlerts(userId),
      async (url) => {
        const response = await axios.get<PredictionAlertListResponse>(url, {
          params: { user_id: userId },
          headers: JSON_HEADERS,
        })
        return mapList(response.data)
      },
    ),

  createAlert: async (
    data: CreatePredictionAlertRequest,
  ): Promise<PredictionAlert> =>
    fromApiOrSimulate(
      PREDICTION_ALERTS_PATH,
      () => simulateCreateAlert(data),
      async (url) => {
        const response = await axios.post<PredictionAlertApiRecord>(
          url,
          toCreateApiPayload(data),
          { headers: JSON_HEADERS },
        )
        return requireUiAlert(response.data)
      },
    ),

  updateAlert: async (
    alertId: string,
    data: UpdatePredictionAlertRequest,
  ): Promise<PredictionAlert> =>
    fromApiOrSimulate(
      itemPath(alertId),
      () => simulateUpdateAlert(alertId, data),
      async (url) => {
        const response = await axios.put<PredictionAlertApiRecord>(
          url,
          toUpdateApiPayload(data),
          { headers: JSON_HEADERS },
        )
        return requireUiAlert(response.data)
      },
    ),

  deleteAlert: async (alertId: string): Promise<void> =>
    fromApiOrSimulate(
      itemPath(alertId),
      () => simulateDeleteAlert(alertId),
      (url) => axios.delete(url, { headers: JSON_HEADERS }).then(() => undefined),
    ),

  toggleStatus: async (alertId: string): Promise<PredictionAlert> =>
    fromApiOrSimulate(
      itemPath(alertId),
      () => simulateToggleStatus(alertId),
      async (url) => {
        const current = await axios.get<PredictionAlertApiRecord>(url, {
          headers: JSON_HEADERS,
        })
        const mapped = requireUiAlert(current.data)
        const nextStatus =
          mapped.status === 'active' || mapped.status === 'triggered'
            ? 'disabled'
            : 'active'
        const response = await axios.put<PredictionAlertApiRecord>(
          url,
          { status: nextStatus },
          { headers: JSON_HEADERS },
        )
        return requireUiAlert(response.data)
      },
    ),

  getHistory: async (userId: string, params?: HistoryQuery) =>
    fromApiOrSimulate(
      PREDICTION_ALERTS_PATH,
      () => simulateGetHistory(userId, params),
      async () => ({
        history: [],
        total: 0,
        page: params?.page || 1,
        totalPages: 0,
      }),
    ),

  exportHistory: async (
    userId: string,
    params?: { startDate?: string; endDate?: string; horizon?: '24h' | '7d' },
  ): Promise<Blob> =>
    fromApiOrSimulate(
      PREDICTION_ALERTS_PATH,
      () => simulateExportHistory(userId, params),
      async () => new Blob([''], { type: 'text/csv' }),
    ),
}
