import React from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

export type AlertStatus = 'active' | 'triggered' | 'disabled' | 'expired';

interface AlertStatusBadgeProps {
  status: AlertStatus;
  className?: string;
  size?: 'sm' | 'default';
}

const statusConfig: Record<AlertStatus, { label: string; className: string; dot: string }> = {
  active: {
    label: 'Active',
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    dot: 'bg-green-500',
  },
  triggered: {
    label: 'Triggered',
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    dot: 'bg-blue-500',
  },
  disabled: {
    label: 'Disabled',
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800/50 dark:text-gray-400',
    dot: 'bg-gray-500',
  },
  expired: {
    label: 'Expired',
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    dot: 'bg-yellow-500',
  },
};

export const AlertStatusBadge: React.FC<AlertStatusBadgeProps> = ({
  status,
  className,
  size = 'default',
}) => {
  const config = statusConfig[status];

  return (
    <Badge
      variant="secondary"
      className={cn(
        'inline-flex items-center gap-1.5 font-medium',
        config.className,
        size === 'sm' ? 'px-2 py-0 text-xs' : 'px-2.5 py-0.5 text-sm',
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
      {config.label}
    </Badge>
  );
};