import type { NewAlertType } from '@/types/alerts'

/** Temporary until auth lands — the seed user that has alerts. */
export const ALERTS_USER_ID = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9'

/** The button reads "New"; the kind it makes is spelled out for screen readers. */
export const CREATE_ALERT_LABELS: Record<NewAlertType, string> = {
  price: 'New price alert',
  macro: 'New macro alert',
  prediction: 'New prediction alert',
}
