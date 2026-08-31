import { describe, expect, it } from 'vitest'
import { formatUnreadBadgeCount } from '@/lib/alerts/formatUnreadBadgeCount'

describe('formatUnreadBadgeCount', () => {
  it('hides the badge when nothing is unread', () => {
    expect(formatUnreadBadgeCount(0)).toBeNull()
  })

  it('shows the raw count under 100', () => {
    expect(formatUnreadBadgeCount(3)).toBe('3')
  })

  it('caps the label at 99+', () => {
    expect(formatUnreadBadgeCount(100)).toBe('99+')
  })
})
