import { Bell } from 'lucide-react'
import { AlertRepeatBadge } from '@/components/alerts/shared/AlertRepeatBadge'
import { AlertRowDeleteButton } from '@/components/alerts/shared/AlertRowDeleteButton'
import { AlertStatusBadge } from '@/components/alerts/shared/AlertStatusBadge'
import { AlertStatusToggle } from '@/components/alerts/shared/AlertStatusToggle'
import { AlertTableNameCell } from '@/components/alerts/shared/AlertTableNameCell'
import { AlertTableRow } from '@/components/alerts/shared/AlertTableRow'
import { formatPriceAlertHeadline } from './priceAlertRule'
import type { PriceAlert } from '@/types/alerts/priceAlert'

type PriceAlertRowProps = {
  alert: PriceAlert
  onDelete: (alert: PriceAlert) => void
  onEdit?: (alert: PriceAlert) => void
  onToggleStatus?: (alert: PriceAlert) => void
}

export function PriceAlertRow({
  alert,
  onDelete,
  onEdit,
  onToggleStatus,
}: PriceAlertRowProps) {
  const name = alert.name?.trim() || alert.asset
  const description = alert.description?.trim() || ''
  const headline = formatPriceAlertHeadline(alert.asset, alert.alert_type, alert.threshold_price)
  const triggeredAt = alert.triggered_at ? new Date(alert.triggered_at).toLocaleString() : ''

  return (
    <AlertTableRow onOpen={onEdit ? () => onEdit(alert) : undefined}>
      <td className="px-4 py-3">
        <AlertTableNameCell
          icon={Bell}
          name={name}
          secondary={description}
          onOpen={onEdit ? () => onEdit(alert) : undefined}
          openLabel="Edit alert"
        />
      </td>
      <td className="px-4 py-3">
        <p className="text-sm">{headline}</p>
        {triggeredAt ? (
          <p className="text-xs text-muted-foreground">Triggered {triggeredAt}</p>
        ) : null}
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">
          <AlertRepeatBadge oneTime={Boolean(alert.one_time)} />
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">
          {onToggleStatus ? (
            <AlertStatusToggle status={alert.status} onToggle={() => onToggleStatus(alert)} />
          ) : (
            <AlertStatusBadge status={alert.status} size="sm" />
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <AlertRowDeleteButton onClick={() => onDelete(alert)} />
      </td>
    </AlertTableRow>
  )
}
