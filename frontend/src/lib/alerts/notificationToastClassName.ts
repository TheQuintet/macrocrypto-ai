import type { NotificationType } from '@/types/alerts/notifications'

/** Solid toast fill classes, matching inbox type colors (blue / purple / green). */
const TOAST_TYPE_CLASS: Record<NotificationType, string> = {
  price_alert:
    '!bg-[var(--toast-price-bg)] !text-[var(--toast-price-text)] [&_[data-icon]]:!text-[var(--toast-price-text)]',
  prediction_alert:
    '!bg-[var(--toast-forecast-bg)] !text-[var(--toast-forecast-text)] [&_[data-icon]]:!text-[var(--toast-forecast-text)]',
  confidence_alert:
    '!bg-[var(--toast-forecast-bg)] !text-[var(--toast-forecast-text)] [&_[data-icon]]:!text-[var(--toast-forecast-text)]',
  macro_alert:
    '!bg-[var(--toast-macro-bg)] !text-[var(--toast-macro-text)] [&_[data-icon]]:!text-[var(--toast-macro-text)]',
}

export function notificationToastClassName(type: NotificationType): string {
  return TOAST_TYPE_CLASS[type]
}
