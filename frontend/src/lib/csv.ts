/**
 * Quote a CSV field.
 *
 * Commas, quotes, and newlines all break a naive join, and a leading `=`,
 * `+`, `-` or `@` is executed as a formula by Excel and Sheets when the file
 * is opened — so those are prefixed with a quote character rather than shipped
 * as-is. A regime reason is free text from the service; it is not trusted to
 * be spreadsheet-safe.
 */
export function csvField(value: unknown): string {
  if (value == null) {
    return ''
  }

  const text = String(value)
  const injectionRisk = /^[=+\-@\t\r]/.test(text)
  const escaped = text.replace(/"/g, '""')

  if (injectionRisk) {
    return `"'${escaped}"`
  }

  if (/[",\n\r]/.test(text)) {
    return `"${escaped}"`
  }

  return escaped
}

export function csvRow(values: readonly unknown[]): string {
  return values.map(csvField).join(',')
}

/** Rows joined with CRLF, which is what RFC 4180 and Excel both expect. */
export function toCsv(rows: readonly (readonly unknown[])[]): string {
  return rows.map(csvRow).join('\r\n')
}

/** `regime-performance-2024-06-15.csv` */
export function csvFileName(prefix: string, nowMs = Date.now()): string {
  const stamp = new Date(nowMs).toISOString().slice(0, 10)

  return `${prefix}-${stamp}.csv`
}
