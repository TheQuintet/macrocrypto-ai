// src/components/alerts/prediction/PredictionHistory.tsx (UPDATED)

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, TrendingUp } from 'lucide-react';
import { showToast } from '@/components/alerts/shared/ToastNotification';
import { SearchBar } from '@/components/alerts/shared/SearchBar';
import { DateRangeFilter } from '@/components/alerts/shared/DateRangeFilter';
import { Pagination } from '@/components/alerts/shared/Pagination';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { predictionAlertApi } from '@/api/alerts/predictionAlerts';
import type {
  PredictionAlertHistory as HistoryType,
  PredictionHorizon,
  PredictionThreshold,
} from '@/types/alerts/predictionAlert';
import { HORIZON_SHORT_LABELS, THRESHOLD_LABELS } from './predictionAlertRule';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface PredictionHistoryProps {
  userId: string;
}

const HORIZON_FILTER_OPTIONS: Array<{ value: PredictionHorizon | 'all'; label: string }> = [
  { value: 'all', label: 'All Horizons' },
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
];

const THRESHOLD_FILTER_OPTIONS: Array<{ value: PredictionThreshold | 'all'; label: string }> = [
  { value: 'all', label: 'All Thresholds' },
  { value: 1, label: '1%' },
  { value: 2, label: '2%' },
  { value: 5, label: '5%' },
  { value: 10, label: '10%' },
];

export function PredictionHistory({ userId }: PredictionHistoryProps) {
  const [history, setHistory] = useState<HistoryType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [horizonFilter, setHorizonFilter] = useState<PredictionHorizon | 'all'>('all');
  const [thresholdFilter, setThresholdFilter] = useState<PredictionThreshold | 'all'>('all');
  const [isExporting, setIsExporting] = useState(false);

  const fetchHistory = async (page = currentPage) => {
    setIsLoading(true);
    try {
      const result = await predictionAlertApi.getHistory(userId, {
        page,
        limit: 10,
        search: searchQuery || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        horizon: horizonFilter !== 'all' ? horizonFilter : undefined,
        threshold: thresholdFilter !== 'all' ? thresholdFilter : undefined,
      });
      setHistory(result.history);
      setTotal(result.total);
      setTotalPages(result.totalPages);
      setCurrentPage(result.page);
    } catch {
      showToast.error('Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

useEffect(() => {
  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const result = await predictionAlertApi.getHistory(userId, {
        page: 1,
        limit: 10,
        search: searchQuery || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        horizon: horizonFilter !== 'all' ? horizonFilter : undefined,
        threshold: thresholdFilter !== 'all' ? thresholdFilter : undefined,
      });
      setHistory(result.history);
      setTotal(result.total);
      setTotalPages(result.totalPages);
      setCurrentPage(result.page);
    } catch {
      showToast.error('Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

  loadHistory();
   
}, [userId, searchQuery, startDate, endDate, horizonFilter, thresholdFilter]);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const blob = await predictionAlertApi.exportHistory(userId, {
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        horizon: horizonFilter !== 'all' ? horizonFilter : undefined,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `prediction-alert-history-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      showToast.success('History exported');
    } catch {
      showToast.error('Failed to export history');
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading && history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-10 w-full" />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <CardTitle>Prediction Alert History ({total})</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={handleExport}
          disabled={isExporting || history.length === 0}
        >
          <Download className="w-4 h-4 mr-2" />
          {isExporting ? 'Exporting...' : 'Export'}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filters - All in ONE row with even spacing */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search - takes remaining space */}
          <div className="flex-1 min-w-[160px]">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search alerts..."
              className="w-full"
            />
          </div>
          
          {/* Date Range - inline with search */}
          <div className="flex-shrink-0">
            <DateRangeFilter
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
            />
          </div>
          
          {/* Horizon Filter */}
          <div className="flex-shrink-0">
            <Select 
              value={horizonFilter} 
              onValueChange={(v) => setHorizonFilter(v as PredictionHorizon | 'all')}
            >
              <SelectTrigger className="h-9 w-[130px] text-sm">
                <SelectValue placeholder="Horizon" />
              </SelectTrigger>
              <SelectContent>
                {HORIZON_FILTER_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Threshold Filter */}
          <div className="flex-shrink-0">
            <Select 
              value={String(thresholdFilter)} 
              onValueChange={(v) => setThresholdFilter(v === 'all' ? 'all' : Number(v) as PredictionThreshold)}
            >
              <SelectTrigger className="h-9 w-[130px] text-sm">
                <SelectValue placeholder="Threshold" />
              </SelectTrigger>
              <SelectContent>
                {THRESHOLD_FILTER_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={String(opt.value)}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* History Table */}
        {history.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            <TrendingUp className="mx-auto h-8 w-8 opacity-50 mb-2" />
            <p>No history records found</p>
            <p className="text-sm">Prediction alerts that trigger will appear here</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-xs font-medium text-muted-foreground">
                    <th className="px-3 py-2 text-left">Previous</th>
                    <th className="px-3 py-2 text-left">New</th>
                    <th className="px-3 py-2 text-center">Change</th>
                    <th className="px-3 py-2 text-center">Horizon</th>
                    <th className="px-3 py-2 text-center">Threshold</th>
                    <th className="px-3 py-2 text-left">Recommendation</th>
                    <th className="px-3 py-2 text-left">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((record) => {
                    const isUp = record.new_prediction > record.previous_prediction;
                    const absChange = Math.abs(record.change_percentage);
                    return (
                      <tr key={record.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="px-3 py-2 font-medium">
                          {record.previous_prediction.toFixed(0)}
                        </td>
                        <td className="px-3 py-2 font-medium">
                          {record.new_prediction.toFixed(0)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <Badge
                            variant={isUp ? 'default' : 'destructive'}
                            className="text-xs"
                          >
                            {isUp ? '+' : ''}{absChange.toFixed(1)}%
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-center text-muted-foreground">
                          {HORIZON_SHORT_LABELS[record.horizon]}
                        </td>
                        <td className="px-3 py-2 text-center text-muted-foreground">
                          {THRESHOLD_LABELS[record.threshold]}
                        </td>
                        <td className="px-3 py-2 max-w-[180px] truncate text-muted-foreground">
                          {record.recommendation}
                        </td>
                        <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">
                          {new Date(record.triggered_at).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center pt-4">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={(page) => {
                    setCurrentPage(page);
                    fetchHistory(page);
                  }}
                />
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}