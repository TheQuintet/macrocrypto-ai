import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Bell, Calendar } from 'lucide-react'
import { AlertTypeCard } from './AlertTypeCard'
import type { NewAlertType } from '@/types/alerts'

type AlertTypeSelectorProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelect: (type: NewAlertType) => void
}

/** Step one of creating an alert: pick price or macro event. */
export function AlertTypeSelector({ open, onOpenChange, onSelect }: AlertTypeSelectorProps) {
  const handleSelect = (type: NewAlertType) => {
    onOpenChange(false)
    onSelect(type)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Choose alert type</DialogTitle>
          <DialogDescription>
            Pick what you want to be alerted about.
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-1 gap-4 py-4 sm:grid-cols-2">
          <AlertTypeCard
            icon={<Bell className="h-6 w-6" />}
            title="Price alert"
            description="Get notified when BTC reaches a price level"
            onClick={() => handleSelect('price')}
          />
          <AlertTypeCard
            icon={<Calendar className="h-6 w-6" />}
            title="Macro event alert"
            description="Get notified before major economic events"
            onClick={() => handleSelect('macro')}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
