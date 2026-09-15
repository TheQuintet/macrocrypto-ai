import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { downloadTextFile } from '@/lib/downloadFile'
import {
  ACTIVE_EXPORT_ROW,
  clickExport,
  expectDownloaded,
  expectExportDisabled,
  expectExportEnabled,
  expectToast,
  exportRow,
  renderExportButton,
} from '@/components/dashboard/regime/RegimeExportButton.testHelpers'

vi.mock('@/lib/downloadFile', () => ({ downloadTextFile: vi.fn() }))

const download = vi.mocked(downloadTextFile)

function downloadCalls() {
  return download.mock.calls.map(([fileName, contents]) => ({
    fileName,
    contents,
  }))
}

describe('RegimeExportButton', () => {
  beforeEach(() => {
    download.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('downloads a dated CSV when clicked', async () => {
    renderExportButton([exportRow()])

    await clickExport()

    await expectDownloaded(downloadCalls(), /^regime-performance-\d{4}-\d{2}-\d{2}\.csv$/)
  })

  it('exports every metric the table shows', async () => {
    renderExportButton([exportRow()])

    await clickExport()

    const { contents } = await expectDownloaded(downloadCalls(), /\.csv$/)
    expect(contents).toContain('Avg return %')
    expect(contents).toContain('28.4')
    expect(contents).toContain('-11.2')
    expect(contents).toContain('1.42')
  })

  it('exports only the rows it was given', async () => {
    // The section hands over the rendered rows, so a filtered view exports
    // filtered data rather than quietly widening to everything.
    renderExportButton([ACTIVE_EXPORT_ROW])

    await clickExport()

    const { contents } = await expectDownloaded(downloadCalls(), /\.csv$/)
    expect(contents).toContain('rising_rates')
    expect(contents).not.toContain('growth')
  })

  it('records the data source and export time in the file', async () => {
    renderExportButton([exportRow()], 'simulated')

    await clickExport()

    const { contents } = await expectDownloaded(downloadCalls(), /\.csv$/)
    expect(contents).toContain('# Data source,Simulated')
    expect(contents).toContain('# Exported at,')
  })

  it('notifies on completion, naming the file and how much it holds', async () => {
    renderExportButton([exportRow(), ACTIVE_EXPORT_ROW])

    await clickExport()

    await expectToast(/regime data exported/i)
    await expectToast(/2 regimes saved to regime-performance-/i)
  })

  it('does not offer an export when there is nothing to export', () => {
    renderExportButton([])

    expectExportDisabled()
  })

  it('offers an export as soon as there are rows', () => {
    renderExportButton([exportRow()])

    expectExportEnabled()
  })

  it('tells the user when the download fails instead of failing silently', async () => {
    download.mockImplementation(() => {
      throw new Error('Blob creation blocked')
    })
    renderExportButton([exportRow()])

    await clickExport()

    await expectToast(/export failed/i)
    await expectToast(/blob creation blocked/i)
  })

  it('re-enables the button after a failure so the user can retry', async () => {
    download.mockImplementationOnce(() => {
      throw new Error('Blob creation blocked')
    })
    renderExportButton([exportRow()])

    await clickExport()
    await expectToast(/export failed/i)

    expectExportEnabled()

    await clickExport()
    expect(download).toHaveBeenCalledTimes(2)
  })
})
