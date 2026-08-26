// src/components/alerts/price/PriceAlertHistory.tsx

import React, { useState } from 'react';
import type { PriceAlertHistory as HistoryType } from '@/types/alerts/priceAlert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DateRangeFilter } from '../shared/DateRangeFilter';
import { SearchBar } from '../shared/SearchBar';
import { Pagination } from '../shared/Pagination';
import { AlertStatusBadge } from '../shared/AlertStatusBadge';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface PriceAlertHistoryProps {
  history: HistoryType[];
  total: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onSearch: (query: string) => void;
  onDateRangeChange: (startDate: string, endDate: string) => void;
  onExport: () => void;
  currentPage: number;
  totalPages: number;
}

export const PriceAlertHistory: React.FC<PriceAlertHistoryProps> = ({
  history,
  total,
  isLoading = false,
  onPageChange,
  onSearch,
  onDateRangeChange,
  onExport,
  currentPage,
  totalPages,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    onSearch(value);
  };

  const handleDateChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    onDateRangeChange(start, end);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <CardTitle>Alert History ({total})</CardTitle>
        <Button variant="outline" size="sm" onClick={onExport}>
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filters */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <SearchBar
            value={searchQuery}
            onChange={handleSearch}
            placeholder="Search alerts..."
            className="flex-1"
          />
          <DateRangeFilter
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={(date) => handleDateChange(date, endDate)}
            onEndDateChange={(date) => handleDateChange(startDate, date)}
          />
        </div>

        {/* History Table */}
        {history.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No history records found
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Event</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Threshold</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">{record.event_type}</TableCell>
                      <TableCell>{record.alert_type}</TableCell>
                      <TableCell>${record.triggered_price?.toFixed(2) ?? '--'}</TableCell>
                      <TableCell>${record.threshold_price?.toFixed(2) ?? '--'}</TableCell>
                      <TableCell>
                        {record.new_status ? (
                          <AlertStatusBadge status={record.new_status} size="sm" />
                        ) : (
                          <span className="text-xs text-muted-foreground">--</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(record.triggered_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center pt-4">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={onPageChange}
                />
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
