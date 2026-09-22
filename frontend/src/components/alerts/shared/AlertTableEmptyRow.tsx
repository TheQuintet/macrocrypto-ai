import type { LucideIcon } from 'lucide-react'
import { useAlertListLayout } from './alertListLayout'

type AlertTableEmptyRowProps = {
  icon: LucideIcon
  message: string
}

export function AlertTableEmptyRow({ icon: Icon, message }: AlertTableEmptyRowProps) {
  const { layout } = useAlertListLayout()

  const body = (
    <>
      <Icon className="mx-auto mb-2 h-8 w-8 opacity-50" />
      <p>{message}</p>
    </>
  )

  if (layout === 'card') {
    return (
      <div className="rounded-lg border px-4 py-12 text-center text-muted-foreground">
        {body}
      </div>
    )
  }

  return (
    <tr>
      <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
        {body}
      </td>
    </tr>
  )
}
