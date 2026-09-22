import { render } from '@testing-library/react'
import { Bell } from 'lucide-react'
import type { ReactNode } from 'react'
import { AlertTable } from './AlertTable'
import { AlertTableEmptyRow } from './AlertTableEmptyRow'
import { AlertTableRow } from './AlertTableRow'

export function renderAlertTable(row?: ReactNode) {
  return render(
    <AlertTable nameLabel="Alert" detailLabel="Trigger">
      {row ?? (
        <AlertTableRow
          name="Breakout"
          detail="BTC/USD hits $80,000"
          repeat="One-time"
          status="Active"
          actions="Delete"
        />
      )}
    </AlertTable>,
  )
}

export function renderEmptyAlertTable() {
  return render(
    <AlertTable nameLabel="Alert" detailLabel="Trigger">
      <AlertTableEmptyRow icon={Bell} message="No alerts found matching your filters" />
    </AlertTable>,
  )
}
