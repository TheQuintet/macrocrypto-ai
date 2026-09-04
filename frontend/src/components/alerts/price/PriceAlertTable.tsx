import { Bell } from 'lucide-react'
import { AlertTable } from '@/components/alerts/shared/AlertTable'
import { AlertTableEmptyRow } from '@/components/alerts/shared/AlertTableEmptyRow'
import { PriceAlertRow } from './PriceAlertRow'
import type { PriceAlert } from '@/types/alerts/priceAlert'

type PriceAlertTableProps = {
  alerts: PriceAlert[]
  onDelete: (alert: PriceAlert) => void
  onEdit?: (alert: PriceAlert) => void
  onToggleStatus?: (alert: PriceAlert) => void
}

export function PriceAlertTable({
  alerts,
  onDelete,
  onEdit,
  onToggleStatus,
}: PriceAlertTableProps) {
  return (
    <AlertTable nameLabel="Alert" detailLabel="Trigger">
      {alerts.length === 0 ? (
        <AlertTableEmptyRow icon={Bell} message="No alerts found matching your filters" />
      ) : (
        alerts.map((alert) => (
          <PriceAlertRow
            key={alert.id}
            alert={alert}
            onDelete={onDelete}
            onEdit={onEdit}
            onToggleStatus={onToggleStatus}
          />
        ))
      )}
    </AlertTable>
  )
}
