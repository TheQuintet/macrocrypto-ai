import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { RegimeViewTabs } from '@/components/dashboard/regime/RegimeViewTabs'
import type { RegimePageView } from '@/types/regime'

export function renderRegimeViewTabs(value: RegimePageView = 'performance') {
  const onChange = vi.fn()

  render(<RegimeViewTabs value={value} onChange={onChange} />)

  return { onChange }
}

export async function selectRegimeViewTab(user: UserEvent, name: string) {
  await user.click(screen.getByRole('tab', { name }))
}

export function expectRegimeViewTabSelected(name: string, selected: boolean) {
  expect(screen.getByRole('tab', { name })).toHaveAttribute(
    'aria-selected',
    String(selected),
  )
}
