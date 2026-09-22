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

/** Solid kind color, so the create button matches the tab it sits under. */
const KIND_BUTTON: Record<NewAlertType, string> = {
  price:
    'bg-[var(--toast-price-bg)] text-[var(--toast-price-text)] hover:bg-[var(--toast-price-bg)]/85',
  prediction:
    'bg-[var(--toast-forecast-bg)] text-[var(--toast-forecast-text)] hover:bg-[var(--toast-forecast-bg)]/85',
  macro:
    'bg-[var(--toast-macro-bg)] text-[var(--toast-macro-text)] hover:bg-[var(--toast-macro-bg)]/85',
}

export function alertKindButtonClassName(kind: NewAlertType): string {
  return KIND_BUTTON[kind]
}
