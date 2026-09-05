import { TrendingUp } from 'lucide-react';
import { AlertRepeatBadge } from '@/components/alerts/shared/AlertRepeatBadge';
import { AlertRowDeleteButton } from '@/components/alerts/shared/AlertRowDeleteButton';
import { AlertStatusToggle } from '@/components/alerts/shared/AlertStatusToggle';
import { AlertTableNameCell } from '@/components/alerts/shared/AlertTableNameCell';
import { AlertTableRow } from '@/components/alerts/shared/AlertTableRow';
import { Badge } from '@/components/ui/badge';
import type { PredictionAlert } from '@/types/alerts/predictionAlert';
import { HORIZON_SHORT_LABELS, THRESHOLD_LABELS } from './predictionAlertRule';

type PredictionAlertRowProps = {
  alert: PredictionAlert;
  onDelete: (alert: PredictionAlert) => void;
  onEdit?: (alert: PredictionAlert) => void;
  onToggleStatus?: (alert: PredictionAlert) => void;
};

export function PredictionAlertRow({
  alert,
  onDelete,
  onEdit,
  onToggleStatus,
}: PredictionAlertRowProps) {
  const name = alert.name?.trim() || `${THRESHOLD_LABELS[alert.threshold]} Change`;
  const description = alert.description?.trim() || '';
  const triggeredAt = alert.triggered_at
    ? new Date(alert.triggered_at).toLocaleString()
    : '';

  return (
    <AlertTableRow onOpen={onEdit ? () => onEdit(alert) : undefined}>
      <td className="px-4 py-3">
        <AlertTableNameCell
          icon={TrendingUp}
          name={name}
          secondary={description}
          onOpen={onEdit ? () => onEdit(alert) : undefined}
          openLabel="Edit alert"
          badge={
            <Badge variant="outline" className="shrink-0 text-xs">
              {HORIZON_SHORT_LABELS[alert.horizon]}
            </Badge>
          }
        />
      </td>
      <td className="px-4 py-3">
        <p className="text-sm">
          Change ≥ {THRESHOLD_LABELS[alert.threshold]} ({HORIZON_SHORT_LABELS[alert.horizon]})
        </p>
        <p className="text-xs text-muted-foreground">
          Confidence change ≥ {alert.confidence_change}%
        </p>
        {triggeredAt ? (
          <p className="text-xs text-muted-foreground">Triggered {triggeredAt}</p>
        ) : null}
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">
          <AlertRepeatBadge oneTime={Boolean(alert.one_time)} />
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">
          {onToggleStatus ? (
            <AlertStatusToggle
              status={alert.status}
              onToggle={() => onToggleStatus(alert)}
            />
          ) : (
            <AlertStatusBadge status={alert.status} size="sm" />
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <AlertRowDeleteButton onClick={() => onDelete(alert)} />
      </td>
    </AlertTableRow>
  );
}

// Import missing AlertStatusBadge
import { AlertStatusBadge } from '@/components/alerts/shared/AlertStatusBadge';
