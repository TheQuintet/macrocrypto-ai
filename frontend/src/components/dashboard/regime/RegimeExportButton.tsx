import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { downloadTextFile } from '@/lib/downloadFile'
import { buildRegimeCsv, regimeCsvFileName } from '@/lib/regimeExport'
import type { RegimePerformanceRow, RegimeSource } from '@/types/regime'

type RegimeExportButtonProps = {
  /** Exactly the rows on screen, so the file matches what was exported from. */
  rows: RegimePerformanceRow[]
  source: RegimeSource
}

/** Download the regime metrics currently on screen as CSV. */
export function RegimeExportButton({ rows, source }: RegimeExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false)

  async function exportCsv() {
    if (isExporting || rows.length === 0) {
      return
    }

    setIsExporting(true)

    try {
      const fileName = regimeCsvFileName()
      downloadTextFile(fileName, buildRegimeCsv({ rows, source }))
      toast.success('Regime data exported', {
        description: `${rows.length} ${
          rows.length === 1 ? 'regime' : 'regimes'
        } saved to ${fileName}`,
      })
    } catch (error) {
      // A failed download must say so: the browser gives no feedback of its
      // own when the blob never reaches the disk.
      toast.error('Export failed', {
        description:
          error instanceof Error ? error.message : 'The file was not saved.',
      })
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className="h-8 gap-1.5"
      disabled={isExporting || rows.length === 0}
      aria-label="Export regime data as CSV"
      aria-busy={isExporting}
      onClick={exportCsv}
    >
      {isExporting ? (
        <Loader2 className="size-3.5 animate-spin" />
      ) : (
        <Download className="size-3.5" />
      )}
      {isExporting ? 'Exporting…' : 'Export CSV'}
    </Button>
  )
}
