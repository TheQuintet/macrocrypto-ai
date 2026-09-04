import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'

type AlertTableProps = {
  /** First column header — what the row is ("Alert", "Event"). */
  nameLabel: string
  /** Second column header — what makes it fire ("Trigger", "When"). */
  detailLabel: string
  children: ReactNode
}

/** One column skeleton for every alert list: name, detail, repeat, status, actions. */
export function AlertTable({ nameLabel, detailLabel, children }: AlertTableProps) {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
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
            <tbody>{children}</tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
