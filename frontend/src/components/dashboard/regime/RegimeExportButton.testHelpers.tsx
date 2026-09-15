import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect } from 'vitest'
import { RegimeExportButton } from '@/components/dashboard/regime/RegimeExportButton'
import { AppToaster } from '@/components/layout/AppToaster'
import type { RegimePerformanceRow, RegimeSource } from '@/types/regime'

export function exportRow(
  overrides: Partial<RegimePerformanceRow> = {},
): RegimePerformanceRow {
  return {
    regimeId: 4,
    regimeType: 'growth',
    startDate: '2023-08-01',
    endDate: '2024-02-29',
    status: 'completed',
    performance: {
      avgReturn: 28.4,
      maxDrawdown: -11.2,
      volatility: 36.8,
      sharpeRatio: 1.42,
      btcPriceStart: 47_800,
      btcPriceEnd: 61_400,
    },
    ...overrides,
  }
}

export const ACTIVE_EXPORT_ROW = exportRow({
  regimeId: 5,
  regimeType: 'rising_rates',
  startDate: '2024-03-01',
  endDate: null,
  status: 'active',
})

/** AppLayout hosts the toaster in the app; mirror it so toasts can render. */
export function renderExportButton(
  rows: RegimePerformanceRow[],
  source: RegimeSource = 'live',
) {
  return render(
    <>
      <RegimeExportButton rows={rows} source={source} />
      <AppToaster />
    </>,
  )
}

export function exportButton() {
  return screen.getByRole('button', { name: /export regime data as csv/i })
}

export async function clickExport() {
  await userEvent.click(exportButton())
}

export function expectExportDisabled() {
  expect(exportButton()).toBeDisabled()
}

export function expectExportEnabled() {
  expect(exportButton()).toBeEnabled()
}

type DownloadCall = { fileName: string; contents: string }

export async function expectDownloaded(
  calls: DownloadCall[],
  fileNamePattern: RegExp,
) {
  await waitFor(() => {
    expect(calls).toHaveLength(1)
  })
  expect(calls[0].fileName).toMatch(fileNamePattern)

  return calls[0]
}

export async function expectToast(pattern: RegExp) {
  await waitFor(
    () => {
      expect(screen.getByText(pattern)).toBeInTheDocument()
    },
    { timeout: 3_000 },
  )
}

export async function expectNoDownload(calls: DownloadCall[]) {
  await waitFor(() => {
    expect(calls).toHaveLength(0)
  })
}
