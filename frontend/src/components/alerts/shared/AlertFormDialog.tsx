import type { FormEvent, ReactNode } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertFormTabs, type AlertFormTab } from './AlertFormTabs'

type AlertFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  titleAccessory?: ReactNode
  toolbar?: ReactNode
  /** Optional alert-kind switch, shown above the tabs while creating. */
  typeSwitcher?: ReactNode
  tab: AlertFormTab
  onTabChange: (tab: AlertFormTab) => void
  alertTab: ReactNode
  advancedTab: ReactNode
  onSubmit: (event: FormEvent) => void
  submitLabel: string
  submitDisabled?: boolean
  isLoading?: boolean
}

/** Shared shell for alert forms: header, Alert/Advanced tabs, footer actions. */
export function AlertFormDialog({
  open,
  onOpenChange,
  title,
  description,
  titleAccessory,
  toolbar,
  typeSwitcher,
  tab,
  onTabChange,
  alertTab,
  advancedTab,
  onSubmit,
  submitLabel,
  submitDisabled = false,
  isLoading = false,
}: AlertFormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between gap-3">
            <DialogTitle>{title}</DialogTitle>
            {titleAccessory}
          </div>
          {description ? <DialogDescription>{description}</DialogDescription> : null}
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4 py-1">
          {toolbar}

          {typeSwitcher}

          <AlertFormTabs value={tab} onChange={onTabChange} />

          {tab === 'alert' ? alertTab : advancedTab}

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              className="min-h-11 sm:min-h-9"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="min-h-11 sm:min-h-9"
              disabled={isLoading || submitDisabled}
            >
              {isLoading ? 'Saving...' : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
