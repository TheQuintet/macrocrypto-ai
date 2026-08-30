import { formatPrice } from '@/components/dashboard/lib/priceFormat'
import type { AlertType } from '@/types/alerts/priceAlert'

export const PRICE_ALERT_ASSET = 'BTC/USD'

export const ALERT_TYPE_OPTIONS: Array<{
  value: AlertType
  label: string
}> = [
  { value: 'reaches', label: 'Hits this price' },
  { value: 'crosses_above', label: 'Goes above' },
  { value: 'crosses_below', label: 'Goes below' },
]

const ALERT_TYPE_VERB: Record<AlertType, string> = {
  reaches: 'hits',
  crosses_above: 'goes above',
  crosses_below: 'goes below',
}

export function formatPriceAlertHeadline(
  asset: string,
  alertType: AlertType,
  threshold: number,
): string {
  return `${asset} ${ALERT_TYPE_VERB[alertType]} ${formatPrice(threshold)}`
}

export function formatAlertPriceInput(value: number): string {
  const amount = Number(value)
  if (!Number.isFinite(amount) || amount <= 0) return ''

  return amount.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/** Last received BTC price, or 0 when the snapshot has nothing usable yet. */
export function proposedAlertThreshold(currentPrice: number | null | undefined): number {
  if (currentPrice == null || !Number.isFinite(currentPrice) || currentPrice <= 0) {
    return 0
  }

  return currentPrice
}

/** Create form: last market price until the user types their own threshold. */
export function resolveAlertThresholdPrice({
  isEditing,
  priceTouched,
  typedPrice,
  lastReceivedPrice,
}: {
  isEditing: boolean
  priceTouched: boolean
  typedPrice: number
  lastReceivedPrice: number | null | undefined
}): number {
  if (isEditing || priceTouched) return typedPrice

  const proposed = proposedAlertThreshold(lastReceivedPrice)
  return proposed > 0 ? proposed : typedPrice
}

export function parseAlertPriceInput(raw: string): number {
  const normalized = raw.replace(/,/g, '').trim()
  if (!normalized) return 0

  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : 0
}

export function isAlertPriceInputValue(raw: string): boolean {
  return raw === '' || /^[0-9,]*\.?[0-9]*$/.test(raw)
}

export function getAlertTypeOption(alertType: AlertType) {
  return ALERT_TYPE_OPTIONS.find((option) => option.value === alertType) ?? ALERT_TYPE_OPTIONS[0]
}
