// frontend/src/components/alerts/prediction/PredictionAlertForm.tsx

import { useState, type FormEvent, type ReactNode } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle } from 'lucide-react';
import { AlertFormDialog } from '@/components/alerts/shared/AlertFormDialog';
import { AlertNotificationFields } from '@/components/alerts/shared/AlertNotificationFields';
import { AlertOneTimeField } from '@/components/alerts/shared/AlertOneTimeField';
import { AlertStatusBadge } from '@/components/alerts/shared/AlertStatusBadge';
import { isAlertEnabled, resolveAlertStatus } from '@/components/alerts/shared/alertStatus';
import { cn } from '@/lib/utils';
import type {
  CreatePredictionAlertRequest,
  PredictionAlert,
  PredictionHorizon,
  PredictionThreshold,
  UpdatePredictionAlertRequest,
} from '@/types/alerts/predictionAlert';
import {
  HORIZON_LABELS,
  THRESHOLD_LABELS,
  THRESHOLD_OPTIONS,
  DEFAULT_CONFIDENCE_CHANGE,
} from './predictionAlertRule';

const HORIZON_OPTIONS: PredictionHorizon[] = ['24h', '7d'];

interface PredictionAlertFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  editingAlert?: PredictionAlert | null;
  onSubmit: (data: CreatePredictionAlertRequest | UpdatePredictionAlertRequest) => Promise<void>;
  isLoading?: boolean;
  typeSwitcher?: ReactNode;
}

const getInitialFormData = (
  userId: string,
  editingAlert?: PredictionAlert | null,
): CreatePredictionAlertRequest => {
  if (editingAlert) {
    return {
      user_id: userId,
      threshold: editingAlert.threshold,
      horizon: editingAlert.horizon,
      confidence_change: editingAlert.confidence_change,
      one_time: editingAlert.one_time,
      name: editingAlert.name || '',
      description: editingAlert.description || '',
      notify_in_app: editingAlert.notify_in_app,
      notify_email: editingAlert.notify_email,
    };
  }

  return {
    user_id: userId,
    threshold: 5,
    horizon: '24h',
    confidence_change: DEFAULT_CONFIDENCE_CHANGE,
    one_time: true,
    name: '',
    description: '',
    notify_in_app: true,
    notify_email: false,
  };
};

export function PredictionAlertForm({
  open,
  onOpenChange,
  userId,
  editingAlert,
  onSubmit,
  isLoading = false,
  typeSwitcher,
}: PredictionAlertFormProps) {
  const isEditing = !!editingAlert;
  const [formData, setFormData] = useState<CreatePredictionAlertRequest>(
    getInitialFormData(userId, editingAlert),
  );
  const [alertStatus, setAlertStatus] = useState(
    resolveAlertStatus(editingAlert?.status) ?? 'active',
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [sessionOpen, setSessionOpen] = useState(open);

  if (sessionOpen !== open) {
    setSessionOpen(open);
    if (open) {
      setFormData(getInitialFormData(userId, editingAlert));
      setAlertStatus(resolveAlertStatus(editingAlert?.status) ?? 'active');
      setErrors({});
      setAdvancedOpen(false);
    }
  }

  const resetForm = () => {
    setFormData(getInitialFormData(userId, editingAlert));
    setAlertStatus(resolveAlertStatus(editingAlert?.status) ?? 'active');
    setErrors({});
    setAdvancedOpen(false);
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      resetForm();
    } else {
      setFormData(getInitialFormData(userId, editingAlert));
      setAlertStatus(resolveAlertStatus(editingAlert?.status) ?? 'active');
      setErrors({});
      setAdvancedOpen(false);
    }
    onOpenChange(newOpen);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.threshold) {
      newErrors.threshold = 'Select a threshold percentage.';
    }

    if (!formData.horizon) {
      newErrors.horizon = 'Select a horizon.';
    }

    if (formData.confidence_change < 1 || formData.confidence_change > 10) {
      newErrors.confidence_change = 'Confidence change must be between 1% and 10%.';
    }

    if (!formData.notify_in_app && !formData.notify_email) {
      newErrors.notify = 'Choose a notification.';
    }

    setErrors(newErrors);
    if (newErrors.notify) {
      setAdvancedOpen(true);
    }
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const submitData = isEditing
      ? {
          threshold: formData.threshold,
          horizon: formData.horizon,
          confidence_change: formData.confidence_change,
          one_time: formData.one_time,
          name: formData.name,
          description: formData.description,
          notify_in_app: formData.notify_in_app,
          notify_email: formData.notify_email,
          status: alertStatus,
        }
      : formData;

    await onSubmit(submitData);
  };

  return (
    <AlertFormDialog
      open={open}
      onOpenChange={handleOpenChange}
      title={isEditing ? 'Edit prediction alert' : 'New prediction alert'}
      titleAccessory={
        isEditing ? <AlertStatusBadge status={alertStatus} size="sm" /> : null
      }
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
      advancedOpen={advancedOpen}
      onAdvancedOpenChange={setAdvancedOpen}
      onSubmit={handleSubmit}
      submitLabel={isEditing ? 'Save changes' : 'Create alert'}
      isLoading={isLoading}
      requiredFields={
        <>
          <fieldset className="space-y-4">
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label id="threshold-label">
                  Threshold <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={String(formData.threshold)}
                  onValueChange={(value) =>
                    setFormData({ ...formData, threshold: Number(value) as PredictionThreshold })
                  }
                >
                  <SelectTrigger
                    aria-labelledby="threshold-label"
                    className={cn('min-h-11 sm:min-h-9', errors.threshold && 'border-destructive')}
                  >
                    <SelectValue placeholder="Select threshold..." />
                  </SelectTrigger>
                  <SelectContent>
                    {THRESHOLD_OPTIONS.map((value) => (
                      <SelectItem key={value} value={String(value)}>
                        {THRESHOLD_LABELS[value]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.threshold ? (
                  <p className="flex items-center gap-1 text-sm text-destructive">
                    <AlertCircle className="h-3 w-3" />
                    {errors.threshold}
                  </p>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label id="horizon-label">
                  Horizon <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={formData.horizon}
                  onValueChange={(value) =>
                    setFormData({ ...formData, horizon: value as PredictionHorizon })
                  }
                >
                  <SelectTrigger
                    aria-labelledby="horizon-label"
                    className={cn('min-h-11 sm:min-h-9', errors.horizon && 'border-destructive')}
                  >
                    <SelectValue placeholder="Select horizon..." />
                  </SelectTrigger>
                  <SelectContent>
                    {HORIZON_OPTIONS.map((value) => (
                      <SelectItem key={value} value={value}>
                        {HORIZON_LABELS[value]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.horizon ? (
                  <p className="flex items-center gap-1 text-sm text-destructive">
                    <AlertCircle className="h-3 w-3" />
                    {errors.horizon}
                  </p>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confidence_change">
                  Confidence change threshold <span className="text-destructive">*</span>
                </Label>
                <div className="relative">
                  <Input
                    id="confidence_change"
                    type="number"
                    min={1}
                    max={10}
                    step={1}
                    placeholder="5"
                    aria-invalid={Boolean(errors.confidence_change)}
                    className={cn(
                      'min-h-11 sm:min-h-9 pr-12',
                      errors.confidence_change && 'border-destructive',
                    )}
                    value={formData.confidence_change}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        confidence_change: Number(e.target.value) || 0,
                      })
                    }
                    disabled={isLoading}
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    %
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">Alert when confidence changes by this percentage (1-10%)</p>
                {errors.confidence_change ? (
                  <p className="flex items-center gap-1 text-sm text-destructive">
                    <AlertCircle className="h-3 w-3" />
                    {errors.confidence_change}
                  </p>
                ) : null}
              </div>
            </div>
          </fieldset>

          <AlertOneTimeField
            checked={formData.one_time ?? false}
            onChange={(checked) => setFormData({ ...formData, one_time: checked })}
            disabled={isLoading}
          />
        </>
      }
      advancedFields={
        <div className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="Bullish breakout alert"
              className="min-h-11 sm:min-h-9"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Note</Label>
            <Textarea
              id="description"
              placeholder="Optional"
              className="min-h-11 sm:min-h-9"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
  );
}