import type { LucideIcon } from 'lucide-react'

type AlertTableEmptyRowProps = {
  icon: LucideIcon
  message: string
}

export function AlertTableEmptyRow({ icon: Icon, message }: AlertTableEmptyRowProps) {
  return (
    <tr>
      <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
        <Icon className="mx-auto mb-2 h-8 w-8 opacity-50" />
        <p>{message}</p>
      </td>
    </tr>
  )
}
