import { describe, expect, it } from 'vitest'
import { csvField, csvFileName, csvRow, toCsv } from '@/lib/csv'

describe('csvField', () => {
  it('leaves an ordinary value alone', () => {
    expect(csvField('Growth')).toBe('Growth')
    expect(csvField(28.4)).toBe('28.4')
  })

  it('writes an empty cell for a missing value', () => {
    expect(csvField(null)).toBe('')
    expect(csvField(undefined)).toBe('')
  })

  it('does not write a missing number as zero', () => {
    // A regime with no measured Sharpe must not read as a Sharpe of 0.
    expect(csvField(null)).not.toBe('0')
  })

  it('quotes a value containing a comma', () => {
    expect(csvField('Rates fell, inflation eased')).toBe(
      '"Rates fell, inflation eased"',
    )
  })

  it('doubles embedded quotes', () => {
    expect(csvField('a "quoted" word')).toBe('"a ""quoted"" word"')
  })

  it('quotes a value containing a newline', () => {
    expect(csvField('line one\nline two')).toBe('"line one\nline two"')
  })

  it('defuses a value a spreadsheet would run as a formula', () => {
    // Reason text comes from the service; it is not trusted to be safe to
    // open in Excel.
    expect(csvField('=SUM(A1:A9)')).toBe('"\'=SUM(A1:A9)"')
    expect(csvField('+1')).toBe('"\'+1"')
    expect(csvField('@import')).toBe('"\'@import"')
  })

  it('defuses a leading minus without mangling a negative number', () => {
    // Both are quoted, so the cell still reads as -12.7 to a human.
    expect(csvField('-12.7')).toBe('"\'-12.7"')
    expect(csvField(-12.7)).toBe('"\'-12.7"')
  })
})

describe('csvRow and toCsv', () => {
  it('joins fields with commas', () => {
    expect(csvRow(['Growth', 28.4, null])).toBe('Growth,28.4,')
  })

  it('joins rows with CRLF, as RFC 4180 and Excel expect', () => {
    expect(toCsv([['a', 'b'], ['c', 'd']])).toBe('a,b\r\nc,d')
  })

  it('renders an empty row as a blank line', () => {
    expect(toCsv([['a'], [], ['b']])).toBe('a\r\n\r\nb')
  })
})

describe('csvFileName', () => {
  it('stamps the file with the export date', () => {
    expect(csvFileName('regime-performance', Date.parse('2024-06-15T09:00:00Z')))
      .toBe('regime-performance-2024-06-15.csv')
  })
})
