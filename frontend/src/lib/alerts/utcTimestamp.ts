const HAS_TIME_ZONE = /(Z|[+-]\d{2}:?\d{2})$/i
const HAS_TIME = /T\d{2}:\d{2}/

/**
 * alert-service sends naive UTC datetimes (`isoformat()` with no offset), and
 * `Date.parse` reads those as local time. Mark them as UTC; leave values that
 * already carry a zone, date-only values and empty strings unchanged.
 */
export function asUtcTimestamp(value: string): string {
  if (!HAS_TIME.test(value) || HAS_TIME_ZONE.test(value)) return value
  return `${value}Z`
}
