import { render } from '@testing-library/react'
import { vi } from 'vitest'
import { PredictionAlertDeleteConfirmation } from './PredictionAlertDeleteConfirmation'
import type { PredictionAlert } from '@/types/alerts/predictionAlert'

export const mockPredictionAlert: PredictionAlert = {
  id: '1',
  user_id: 'user-1',
  threshold: 5,
  horizon: '24h',
  confidence_change: 5,
  direction: 'both',
  asset: 'BTC/USD',
  status: 'active',
  one_time: false,
  name: 'Bullish Breakout',
  description: 'Strong upward movement',
  notify_in_app: true,
  notify_email: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

type RenderArgs = {
  alert?: PredictionAlert | null
  isLoading?: boolean
}

export function renderPredictionAlertDeleteConfirmation(overrides: RenderArgs = {}) {
  const onOpenChange = vi.fn()
  const onConfirm = vi.fn()

  const view = render(
    <PredictionAlertDeleteConfirmation
      alert={overrides.alert === undefined ? mockPredictionAlert : overrides.alert}
      onOpenChange={onOpenChange}
      onConfirm={onConfirm}
      isLoading={overrides.isLoading}
    />,
  )

  return { ...view, onOpenChange, onConfirm }
}
