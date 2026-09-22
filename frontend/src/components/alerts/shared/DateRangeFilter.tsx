// src/components/alerts/shared/DateRangeFilter.tsx (UPDATED)

import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  className?: string;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  className,
}) => {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex items-center gap-1.5">
        <Label htmlFor="start-date" className="text-xs text-muted-foreground whitespace-nowrap">
          From
        </Label>
        <Input
          id="start-date"
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="h-9 w-[145px] text-sm"
        />
      </div>
      <div className="flex items-center gap-1.5">
        <Label htmlFor="end-date" className="text-xs text-muted-foreground whitespace-nowrap">
          To
        </Label>
        <Input
          id="end-date"
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className="h-9 w-[145px] text-sm"
        />
      </div>
    </div>
  );
};