import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
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
import { AlertCircle, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PriceAlert, AlertType, CreatePriceAlertRequest, UpdatePriceAlertRequest } from '@/types/alerts/priceAlert';

interface PriceAlertFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  editingAlert?: PriceAlert | null;
  onSubmit: (data: CreatePriceAlertRequest | UpdatePriceAlertRequest) => Promise<void>;
  onPreview?: () => void;
  isLoading?: boolean;
}

const alertTypeOptions: Array<{ value: AlertType; label: string }> = [
  { value: 'reaches', label: 'Reaches' },
  { value: 'crosses_above', label: 'Crosses Above' },
  { value: 'crosses_below', label: 'Crosses Below' },
];

const getInitialFormData = (userId: string, editingAlert?: PriceAlert | null): CreatePriceAlertRequest => {
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
    };
  }
  return {
    user_id: userId,
    threshold_price: 0,
    alert_type: 'reaches',
    asset: 'BTC/USD',
    one_time: true,
    name: '',
    description: '',
    notify_in_app: true,
    notify_email: false,
  };
};

export const PriceAlertForm: React.FC<PriceAlertFormProps> = ({
  open,
  onOpenChange,
  userId,
  editingAlert,
  onSubmit,
  onPreview,
  isLoading = false,
}) => {
  const isEditing = !!editingAlert;

  const [formData, setFormData] = useState<CreatePriceAlertRequest>(
    getInitialFormData(userId, editingAlert)
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when editingAlert or userId changes
  const resetForm = () => {
    setFormData(getInitialFormData(userId, editingAlert));
    setErrors({});
  };

  // Update form when editingAlert changes (but only when dialog opens)
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      // Closing - reset form
      resetForm();
    } else {
      // Opening - set initial data
      setFormData(getInitialFormData(userId, editingAlert));
      setErrors({});
    }
    onOpenChange(newOpen);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.threshold_price || formData.threshold_price <= 0) {
      newErrors.threshold_price = 'Threshold must be greater than 0';
    }

    if (!formData.alert_type) {
      newErrors.alert_type = 'Please select an alert type';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

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
      : formData;

    await onSubmit(submitData);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Price Alert' : 'Create Price Alert'}</DialogTitle>
          {editingAlert?.status && (
            <p className="text-sm text-muted-foreground">
              Current status: <span className="font-medium">{editingAlert.status}</span>
            </p>
          )}
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          {/* Threshold Price */}
          <div className="space-y-2">
            <Label htmlFor="threshold_price">
              Threshold Price <span className="text-red-500">*</span>
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
              <Input
                id="threshold_price"
                type="number"
                step="0.01"
                min="0"
                placeholder="Enter threshold price"
                className={cn('pl-7', errors.threshold_price && 'border-red-500')}
                value={formData.threshold_price || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, threshold_price: parseFloat(e.target.value) || 0 })
                }
                disabled={isLoading}
              />
            </div>
            {errors.threshold_price && (
              <p className="text-sm text-red-500 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.threshold_price}
              </p>
            )}
          </div>

          {/* Alert Type */}
          <div className="space-y-2">
            <Label htmlFor="alert_type">
              Alert Type <span className="text-red-500">*</span>
            </Label>
            <Select
              value={formData.alert_type}
              onValueChange={(value: string) => setFormData({ ...formData, alert_type: value as AlertType })}
            >
              <SelectTrigger className={errors.alert_type ? 'border-red-500' : ''}>
                <SelectValue placeholder="Select alert type" />
              </SelectTrigger>
              <SelectContent>
                {alertTypeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.alert_type && (
              <p className="text-sm text-red-500 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.alert_type}
              </p>
            )}
          </div>

          {/* Alert Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Alert Name (Optional)</Label>
            <Input
              id="name"
              placeholder="e.g., BTC Breakout Alert"
              value={formData.name || ''}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setFormData({ ...formData, name: e.target.value })
              }
              disabled={isLoading}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              placeholder="Add a description for this alert"
              value={formData.description || ''}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                setFormData({ ...formData, description: e.target.value })
              }
              disabled={isLoading}
              rows={2}
            />
          </div>

          {/* One-time Toggle */}
          <div className="flex items-center justify-between pt-2 border-t">
            <Label htmlFor="one_time" className="text-sm">One-time alert</Label>
            <Switch
              id="one_time"
              checked={formData.one_time}
              onCheckedChange={(checked: boolean) => setFormData({ ...formData, one_time: checked })}
              disabled={isLoading}
            />
          </div>

          {/* Notification Preferences */}
          <div className="space-y-2 pt-2 border-t">
            <p className="text-sm font-medium">Notifications</p>
            <div className="flex items-center justify-between">
              <Label htmlFor="notify_in_app" className="text-sm font-normal">In-app notification</Label>
              <Switch
                id="notify_in_app"
                checked={formData.notify_in_app}
                onCheckedChange={(checked: boolean) => setFormData({ ...formData, notify_in_app: checked })}
                disabled={isLoading}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="notify_email" className="text-sm font-normal">Email notification</Label>
              <Switch
                id="notify_email"
                checked={formData.notify_email}
                onCheckedChange={(checked: boolean) => setFormData({ ...formData, notify_email: checked })}
                disabled={isLoading}
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            {onPreview && !isEditing && (
              <Button
                type="button"
                variant="outline"
                onClick={onPreview}
                disabled={isLoading}
                className="gap-2"
              >
                <Eye className="w-4 h-4" />
                Preview
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : isEditing ? 'Update Alert' : 'Create Alert'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};