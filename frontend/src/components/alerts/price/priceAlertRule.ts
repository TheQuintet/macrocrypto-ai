import { formatPrice } from '@/components/dashboard/lib/priceFormat'
import type { AlertType } from '@/types/alerts/priceAlert'

export const PRICE_ALERT_ASSET = 'BTC/USD'

export const ALERT_TYPE_OPTIONS: Array<{
  value: AlertType
  label: string
  hint: string
}> = [
  {
    value: 'reaches',
    label: 'Hits this price',
    hint: 'Fires when the latest price equals this level.',
  },
  {
    value: 'crosses_above',
    label: 'Goes above',
    hint: 'Fires when the price moves from below this level to at or above it.',
  },
  {
    value: 'crosses_below',
    label: 'Goes below',
    hint: 'Fires when the price moves from above this level to at or below it.',
  },
]

const ALERT_TYPE_VERB: Record<AlertType, string> = {
  reaches: 'hits',
  crosses_above: 'goes above',
  crosses_below: 'goes below',
}

export function formatPriceAlertRule(
  asset: string,
  alertType: AlertType,
  threshold: number,
): string {
  if (!threshold || threshold <= 0) {
    return 'Enter a price to see when this alert will fire.'
  }

  return `We'll notify you when ${asset} ${ALERT_TYPE_VERB[alertType]} ${formatPrice(threshold)}.`
}

export function getAlertTypeOption(alertType: AlertType) {
  return ALERT_TYPE_OPTIONS.find((option) => option.value === alertType) ?? ALERT_TYPE_OPTIONS[0]
}
