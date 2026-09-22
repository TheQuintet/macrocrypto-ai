import { TrendingUp } from 'lucide-react';
import { AlertTable } from '@/components/alerts/shared/AlertTable';
import { AlertTableEmptyRow } from '@/components/alerts/shared/AlertTableEmptyRow';
import { PredictionAlertRow } from './PredictionAlertRow';
import type { PredictionAlert } from '@/types/alerts/predictionAlert';

type PredictionAlertTableProps = {
  alerts: PredictionAlert[];
  onDelete: (alert: PredictionAlert) => void;
  onEdit?: (alert: PredictionAlert) => void;
  onToggleStatus?: (alert: PredictionAlert) => void;
};

export function PredictionAlertTable({
  alerts,
  onDelete,
  onEdit,
  onToggleStatus,
}: PredictionAlertTableProps) {
  return (
    <AlertTable nameLabel="Alert" detailLabel="Condition">
      {alerts.length === 0 ? (
        <AlertTableEmptyRow
          icon={TrendingUp}
          message="No prediction alerts found matching your filters"
        />
      ) : (
        alerts.map((alert) => (
          <PredictionAlertRow
            key={alert.id}
            alert={alert}
            onDelete={onDelete}
            onEdit={onEdit}
            onToggleStatus={onToggleStatus}
          />
        ))
      )}
    </AlertTable>
  );
}
