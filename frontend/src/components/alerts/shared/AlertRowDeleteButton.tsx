import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

type AlertRowDeleteButtonProps = {
  onClick: () => void
  disabled?: boolean
  title?: string
}

export function AlertRowDeleteButton({
  onClick,
  disabled = false,
  title = 'Delete alert',
}: AlertRowDeleteButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      aria-label="Delete alert"
      title={title}
      disabled={disabled}
      onClick={onClick}
      className="h-8 w-8 text-red-500 hover:bg-red-50 hover:text-red-700"
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  )
}
