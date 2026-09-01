import { useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react'
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
import { AlertFormDialog } from '@/components/alerts/shared/AlertFormDialog'
import { AlertNotificationFields } from '@/components/alerts/shared/AlertNotificationFields'
import { AlertOneTimeField } from '@/components/alerts/shared/AlertOneTimeField'
import type { AlertFormTab } from '@/components/alerts/shared/AlertFormTabs'
import { isAlertEnabled, resolveAlertStatus } from '@/components/alerts/shared/alertStatus'
import { AlertCircle } from 'lucide-react'
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery'
import { cn } from '@/lib/utils'
import type {
  AlertStatus,
  AlertType,
  CreatePriceAlertRequest,
  PriceAlert,
  UpdatePriceAlertRequest,
} from '@/types/alerts/priceAlert'
import {
  ALERT_TYPE_OPTIONS,
  PRICE_ALERT_ASSET,
  formatAlertPriceInput,
  formatPriceAlertHeadline,
  getAlertTypeOption,
  isAlertPriceInputValue,
  parseAlertPriceInput,
  proposedAlertThreshold,
  resolveAlertThresholdPrice,
} from './priceAlertRule'

interface PriceAlertFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  userId: string
  editingAlert?: PriceAlert | null
  onSubmit: (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => Promise<void>
  isLoading?: boolean
  /** Alert-kind switch, supplied while creating so the kind can be corrected. */
  typeSwitcher?: ReactNode
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

function getInitialPriceText(editingAlert?: PriceAlert | null) {
  return formatAlertPriceInput(editingAlert?.threshold_price ?? 0)
}

export function PriceAlertForm({
  open,
  onOpenChange,
  userId,
  editingAlert,
  onSubmit,
  isLoading = false,
  typeSwitcher,
}: PriceAlertFormProps) {
  const isEditing = !!editingAlert
  const { data: snapshot } = useBtcPriceSnapshotQuery()
  const lastReceivedPrice = snapshot?.currentPrice
  const [formData, setFormData] = useState<CreatePriceAlertRequest>(
    getInitialFormData(userId, editingAlert),
  )
  const [alertStatus, setAlertStatus] = useState<AlertStatus>(
    resolveAlertStatus(editingAlert?.status) ?? 'active',
  )
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [tab, setTab] = useState<AlertFormTab>('alert')
  const [priceText, setPriceText] = useState(getInitialPriceText(editingAlert))
  const [priceTouched, setPriceTouched] = useState(false)
  const [sessionOpen, setSessionOpen] = useState(open)

  if (sessionOpen !== open) {
    setSessionOpen(open)
    if (open) {
      setFormData(getInitialFormData(userId, editingAlert))
      setAlertStatus(resolveAlertStatus(editingAlert?.status) ?? 'active')
      setErrors({})
      setTab('alert')
      setPriceText(getInitialPriceText(editingAlert))
      setPriceTouched(false)
    }
  }

  const thresholdPrice = resolveAlertThresholdPrice({
    isEditing,
    priceTouched,
    typedPrice: formData.threshold_price,
    lastReceivedPrice,
  })
  const displayedPriceText =
    isEditing || priceTouched
      ? priceText
      : formatAlertPriceInput(thresholdPrice)

  const resetForm = () => {
    setFormData(getInitialFormData(userId, editingAlert))
    setAlertStatus(resolveAlertStatus(editingAlert?.status) ?? 'active')
    setErrors({})
    setTab('alert')
    setPriceText(getInitialPriceText(editingAlert))
    setPriceTouched(false)
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      resetForm()
    } else {
      setFormData(getInitialFormData(userId, editingAlert))
      setAlertStatus(resolveAlertStatus(editingAlert?.status) ?? 'active')
      setErrors({})
      setTab('alert')
      setPriceText(getInitialPriceText(editingAlert))
      setPriceTouched(false)
    }
    onOpenChange(newOpen)
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!thresholdPrice || thresholdPrice <= 0) {
      newErrors.threshold_price = 'Enter a price.'
    }

    if (!formData.alert_type) {
      newErrors.alert_type = 'Choose a condition.'
    }

    if (!formData.notify_in_app && !formData.notify_email) {
      newErrors.notify = 'Choose a notification.'
    }

    setErrors(newErrors)
    if (newErrors.notify && !newErrors.threshold_price && !newErrors.alert_type) {
      setTab('advanced')
    } else if (newErrors.threshold_price || newErrors.alert_type) {
      setTab('alert')
    }
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    const submitData = isEditing
      ? {
          threshold_price: thresholdPrice,
          alert_type: formData.alert_type,
          asset: formData.asset,
          one_time: formData.one_time,
          name: formData.name,
          description: formData.description,
          notify_in_app: formData.notify_in_app,
          notify_email: formData.notify_email,
          status: alertStatus,
        }
      : { ...formData, threshold_price: thresholdPrice }

    await onSubmit(submitData)
  }

  const selectedType = getAlertTypeOption(formData.alert_type)
  const ruleSummary = formatPriceAlertHeadline(
    formData.asset ?? PRICE_ALERT_ASSET,
    formData.alert_type,
    thresholdPrice,
  )
  const hasPrice = thresholdPrice > 0

  return (
    <AlertFormDialog
      open={open}
      onOpenChange={handleOpenChange}
      title={isEditing ? 'Edit alert' : 'New alert'}
      titleAccessory={isEditing ? <AlertStatusBadge status={alertStatus} size="sm" /> : null}
      toolbar={
        isEditing ? (
          <div className="flex justify-end">
            <Switch
              size="sm"
              checked={isAlertEnabled(alertStatus)}
              onCheckedChange={(checked) =>
                setAlertStatus(checked ? 'active' : 'disabled')
              }
              aria-label={isAlertEnabled(alertStatus) ? 'Deactivate alert' : 'Activate alert'}
              disabled={isLoading}
            />
          </div>
        ) : null
      }
      typeSwitcher={isEditing ? null : typeSwitcher}
      tab={tab}
      onTabChange={setTab}
      onSubmit={handleSubmit}
      submitLabel={isEditing ? 'Save changes' : 'Create alert'}
      isLoading={isLoading}
      alertTab={
        <>
          <fieldset className="space-y-3 rounded-lg border border-border bg-muted/30 p-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex min-h-11 items-center rounded-md border border-border bg-background px-2.5 text-sm font-medium sm:min-h-9">
                {formData.asset ?? PRICE_ALERT_ASSET}
              </span>
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
                    type="text"
                    inputMode="decimal"
                    placeholder={
                      formatAlertPriceInput(
                        proposedAlertThreshold(lastReceivedPrice),
                      ) || '85,000.00'
                    }
                    aria-invalid={Boolean(errors.threshold_price)}
                    aria-describedby={
                      errors.threshold_price
                        ? 'threshold-price-error'
                        : hasPrice
                          ? 'price-alert-rule'
                          : undefined
                    }
                    className={cn(
                      'min-h-11 pl-7 sm:min-h-9',
                      errors.threshold_price && 'border-destructive',
                    )}
                    value={displayedPriceText}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => {
                      const next = e.target.value
                      if (!isAlertPriceInputValue(next)) return
                      setPriceTouched(true)
                      setPriceText(next)
                      setFormData({
                        ...formData,
                        threshold_price: parseAlertPriceInput(next),
                      })
                    }}
                    onBlur={() => {
                      setPriceText(formatAlertPriceInput(formData.threshold_price))
                    }}
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

            {hasPrice ? (
              <p
                id="price-alert-rule"
                role="status"
                aria-live="polite"
                className="rounded-md bg-primary/5 px-3 py-2 text-sm"
              >
                {ruleSummary}
              </p>
            ) : null}
          </fieldset>

          <AlertOneTimeField
            checked={formData.one_time ?? false}
            onChange={(checked) => setFormData({ ...formData, one_time: checked })}
            disabled={isLoading}
          />
        </>
      }
      advancedTab={
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="BTC breakout"
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
              placeholder="Optional"
              value={formData.description || ''}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                setFormData({ ...formData, description: e.target.value })
              }
              disabled={isLoading}
              rows={2}
            />
          </div>
          <AlertNotificationFields
            notifyInApp={formData.notify_in_app ?? false}
            notifyEmail={formData.notify_email ?? false}
            onNotifyInAppChange={(checked) =>
              setFormData({ ...formData, notify_in_app: checked })
            }
            onNotifyEmailChange={(checked) =>
              setFormData({ ...formData, notify_email: checked })
            }
            error={errors.notify}
            disabled={isLoading}
          />
        </div>
      }
    />
  )
}
