import { useState, type ChangeEvent, type FormEvent } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select'
import { AlertStatusBadge } from '@/components/alerts/shared/AlertStatusBadge'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type {
  AlertType,
  CreatePriceAlertRequest,
  PriceAlert,
  UpdatePriceAlertRequest,
} from '@/types/alerts/priceAlert'
import {
  ALERT_TYPE_OPTIONS,
  PRICE_ALERT_ASSET,
  formatPriceAlertRule,
  getAlertTypeOption,
} from './priceAlertRule'

interface PriceAlertFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  userId: string
  editingAlert?: PriceAlert | null
  onSubmit: (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => Promise<void>
  isLoading?: boolean
}

const getInitialFormData = (
  userId: string,
  editingAlert?: PriceAlert | null,
): CreatePriceAlertRequest => {
  if (editingAlert) {
    return {
      user_id: userId,
      threshold_price: editingAlert.threshold_price,
      alert_type: editingAlert.alert_type,
      asset: editingAlert.asset,
      one_time: editingAlert.one_time,
      name: editingAlert.name || '',
      description: editingAlert.description || '',
      notify_in_app: editingAlert.notify_in_app,
      notify_email: editingAlert.notify_email,
    }
  }

  return {
    user_id: userId,
    threshold_price: 0,
    alert_type: 'reaches',
    asset: PRICE_ALERT_ASSET,
    one_time: true,
    name: '',
    description: '',
    notify_in_app: true,
    notify_email: false,
  }
}

export function PriceAlertForm({
  open,
  onOpenChange,
  userId,
  editingAlert,
  onSubmit,
  isLoading = false,
}: PriceAlertFormProps) {
  const isEditing = !!editingAlert
  const [formData, setFormData] = useState<CreatePriceAlertRequest>(
    getInitialFormData(userId, editingAlert),
  )
  const [errors, setErrors] = useState<Record<string, string>>({})

  const resetForm = () => {
    setFormData(getInitialFormData(userId, editingAlert))
    setErrors({})
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      resetForm()
    } else {
      setFormData(getInitialFormData(userId, editingAlert))
      setErrors({})
    }
    onOpenChange(newOpen)
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.threshold_price || formData.threshold_price <= 0) {
      newErrors.threshold_price = 'Enter a price greater than 0.'
    }

    if (!formData.alert_type) {
      newErrors.alert_type = 'Choose when this alert should fire.'
    }

    if (!formData.notify_in_app && !formData.notify_email) {
      newErrors.notify = 'Choose at least one way to be notified.'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    const submitData = isEditing
      ? {
          threshold_price: formData.threshold_price,
          alert_type: formData.alert_type,
          asset: formData.asset,
          one_time: formData.one_time,
          name: formData.name,
          description: formData.description,
          notify_in_app: formData.notify_in_app,
          notify_email: formData.notify_email,
        }
      : formData

    await onSubmit(submitData)
  }

  const selectedType = getAlertTypeOption(formData.alert_type)
  const ruleSummary = formatPriceAlertRule(
    formData.asset ?? PRICE_ALERT_ASSET,
    formData.alert_type,
    formData.threshold_price,
  )
  const hasPrice = formData.threshold_price > 0

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[520px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-3">
            <DialogTitle>{isEditing ? 'Edit price alert' : 'Create price alert'}</DialogTitle>
            {editingAlert?.status ? (
              <AlertStatusBadge status={editingAlert.status} size="sm" />
            ) : null}
          </div>
          <DialogDescription>
            Set a BTC/USD price rule and how you want to be notified.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-1">
          <fieldset className="space-y-3 rounded-lg border border-border bg-muted/30 p-3">
            <legend className="px-1 text-sm font-medium">When should this fire?</legend>

            <div className="flex items-center gap-2">
              <span className="inline-flex min-h-11 items-center rounded-md border border-border bg-background px-2.5 text-sm font-medium sm:min-h-9">
                {formData.asset ?? PRICE_ALERT_ASSET}
              </span>
              <span className="text-xs text-muted-foreground">Bitcoin priced in US dollars</span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label id="alert-type-label">Condition</Label>
                <Select
                  value={formData.alert_type}
                  onValueChange={(value: string) =>
                    setFormData({ ...formData, alert_type: value as AlertType })
                  }
                >
                  <SelectTrigger
                    aria-labelledby="alert-type-label"
                    className={cn('min-h-11 sm:min-h-9', errors.alert_type && 'border-destructive')}
                  >
                    {selectedType.label}
                  </SelectTrigger>
                  <SelectContent>
                    {ALERT_TYPE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">{selectedType.hint}</p>
                {errors.alert_type ? (
                  <p className="flex items-center gap-1 text-sm text-destructive">
                    <AlertCircle className="h-3 w-3" />
                    {errors.alert_type}
                  </p>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label htmlFor="threshold_price">
                  Price <span className="text-destructive">*</span>
                </Label>
                <div className="relative">
                  <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="threshold_price"
                    type="number"
                    step="0.01"
                    min="0"
                    inputMode="decimal"
                    placeholder="85,000"
                    aria-invalid={Boolean(errors.threshold_price)}
                    aria-describedby={
                      errors.threshold_price ? 'threshold-price-error' : 'price-alert-rule'
                    }
                    className={cn(
                      'min-h-11 pl-7 sm:min-h-9',
                      errors.threshold_price && 'border-destructive',
                    )}
                    value={formData.threshold_price || ''}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setFormData({
                        ...formData,
                        threshold_price: parseFloat(e.target.value) || 0,
                      })
                    }
                    disabled={isLoading}
                  />
                </div>
                {errors.threshold_price ? (
                  <p
                    id="threshold-price-error"
                    className="flex items-center gap-1 text-sm text-destructive"
                  >
                    <AlertCircle className="h-3 w-3" />
                    {errors.threshold_price}
                  </p>
                ) : null}
              </div>
            </div>

            <p
              id="price-alert-rule"
              role="status"
              aria-live="polite"
              className={cn(
                'rounded-md px-3 py-2 text-sm',
                hasPrice ? 'bg-primary/5 text-foreground' : 'bg-background text-muted-foreground',
              )}
            >
              {ruleSummary}
            </p>
          </fieldset>

          <fieldset className="space-y-2 rounded-lg border border-border p-3">
            <legend className="px-1 text-sm font-medium">After it fires</legend>
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <Label htmlFor="one_time">One-time alert</Label>
                <p className="text-xs text-muted-foreground">
                  {formData.one_time
                    ? 'Stops watching after the first time this price is hit.'
                    : 'Keeps watching and can fire again the next time this price is hit.'}
                </p>
              </div>
              <Switch
                id="one_time"
                checked={formData.one_time}
                onCheckedChange={(checked: boolean) =>
                  setFormData({ ...formData, one_time: checked })
                }
                disabled={isLoading}
              />
            </div>
          </fieldset>

          <fieldset className="space-y-3 rounded-lg border border-border p-3">
            <legend className="px-1 text-sm font-medium">How should we notify you?</legend>
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <Label htmlFor="notify_in_app">In the app</Label>
                <p className="text-xs text-muted-foreground">
                  Shows as a notification in MacroCrypto.
                </p>
              </div>
              <Switch
                id="notify_in_app"
                checked={formData.notify_in_app}
                onCheckedChange={(checked: boolean) =>
                  setFormData({ ...formData, notify_in_app: checked })
                }
                disabled={isLoading}
              />
            </div>
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <Label htmlFor="notify_email">Email</Label>
                <p className="text-xs text-muted-foreground">
                  Sent to the email on your account. You do not need to enter an address here.
                </p>
              </div>
              <Switch
                id="notify_email"
                checked={formData.notify_email}
                onCheckedChange={(checked: boolean) =>
                  setFormData({ ...formData, notify_email: checked })
                }
                disabled={isLoading}
              />
            </div>
            {errors.notify ? (
              <p className="flex items-center gap-1 text-sm text-destructive">
                <AlertCircle className="h-3 w-3" />
                {errors.notify}
              </p>
            ) : null}
          </fieldset>

          <fieldset className="space-y-3 rounded-lg border border-dashed border-border p-3">
            <legend className="px-1 text-sm font-medium text-muted-foreground">
              Optional details
            </legend>
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                placeholder="e.g. BTC breakout"
                className="min-h-11 sm:min-h-9"
                value={formData.name || ''}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Note</Label>
              <Textarea
                id="description"
                placeholder="Why you set this alert"
                value={formData.description || ''}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                disabled={isLoading}
                rows={2}
              />
            </div>
          </fieldset>

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              className="min-h-11 sm:min-h-9"
              onClick={() => handleOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" className="min-h-11 sm:min-h-9" disabled={isLoading}>
              {isLoading ? 'Saving...' : isEditing ? 'Save changes' : 'Create alert'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
