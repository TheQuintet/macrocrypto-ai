// src/components/alerts/price/__tests__/testHelpers.ts

import type { PriceAlert, CreatePriceAlertRequest } from '@/types/alerts/priceAlert';

export const mockAlert: PriceAlert = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  user_id: 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9',
  threshold_price: 85000,
  alert_type: 'crosses_above',
  asset: 'BTC/USD',
  status: 'active',
  one_time: true,
  created_at: '2026-08-26T14:31:18.591456',
  updated_at: '2026-08-26T14:31:18.591463',
  triggered_at: null,
  notify_in_app: true,
  notify_email: false,
  name: 'BTC Breakout Alert',
  description: 'Alert when BTC crosses above 85000',
};

export const mockAlerts: PriceAlert[] = [
  mockAlert,
  {
    ...mockAlert,
    id: '223e4567-e89b-12d3-a456-426614174001',
    threshold_price: 75000,
    alert_type: 'crosses_below',
    status: 'triggered',
    triggered_at: '2026-08-26T14:36:31.958869',
  },
];

export const mockCreateRequest: CreatePriceAlertRequest = {
  user_id: 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9',
  threshold_price: 85000,
  alert_type: 'crosses_above',
  asset: 'BTC/USD',
  one_time: true,
  name: 'BTC Breakout Alert',
  description: 'Alert when BTC crosses above 85000',
  notify_in_app: true,
  notify_email: false,
};
