import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { AlertListLayoutContext } from './alertListLayout'

type AlertTableProps = {
  /** First column header — what the row is ("Alert", "Event"). */
  nameLabel: string
  /** Second column header — what makes it fire ("Trigger", "When"). */
  detailLabel: string
  children: ReactNode
}

/** Cards below sm so actions stay on screen; the five-column table from sm up. */
export function AlertTable({ nameLabel, detailLabel, children }: AlertTableProps) {
  const labels = { nameLabel, detailLabel }

  return (
    <div className="space-y-3">
      <AlertListLayoutContext.Provider value={{ ...labels, layout: 'card' }}>
        <div data-slot="alert-list-cards" className="space-y-3 sm:hidden">
          {children}
        </div>
      </AlertListLayoutContext.Provider>

      <Card data-slot="alert-list-table" className="hidden sm:block">
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50 text-xs font-medium text-muted-foreground">
                <th className="min-w-[220px] px-4 py-3 text-left">{nameLabel}</th>
                <th className="min-w-[180px] px-4 py-3 text-left">{detailLabel}</th>
                <th className="min-w-[110px] px-4 py-3 text-center">Repeat</th>
                <th className="min-w-[120px] px-4 py-3 text-center">Status</th>
                <th className="min-w-[90px] px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <AlertListLayoutContext.Provider value={{ ...labels, layout: 'table' }}>
                {children}
              </AlertListLayoutContext.Provider>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
