import type { NewAlertType } from '@/types/alerts'

/**
 * Same tokens as notification toasts: price blue, forecast purple, macro green.
 * Class names must be full string literals so Tailwind can pick them up.
 */

/** Active: solid kind color on underline + label. Idle: softer kind color. */
const KIND_TAB_ACTIVE: Record<NewAlertType, string> = {
  price: 'border-[var(--toast-price-bg)] text-[var(--toast-price-bg)]',
  prediction: 'border-[var(--toast-forecast-bg)] text-[var(--toast-forecast-bg)]',
  macro: 'border-[var(--toast-macro-bg)] text-[var(--toast-macro-bg)]',
}

const KIND_TAB_IDLE: Record<NewAlertType, string> = {
  price:
    'border-transparent text-[var(--toast-price-bg)]/70 hover:text-[var(--toast-price-bg)]',
  prediction:
    'border-transparent text-[var(--toast-forecast-bg)]/70 hover:text-[var(--toast-forecast-bg)]',
  macro:
    'border-transparent text-[var(--toast-macro-bg)]/70 hover:text-[var(--toast-macro-bg)]',
}

export function alertKindTabClassName(kind: NewAlertType, active: boolean): string {
  return active ? KIND_TAB_ACTIVE[kind] : KIND_TAB_IDLE[kind]
}
