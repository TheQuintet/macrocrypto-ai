import { afterEach, describe, expect, it, vi } from 'vitest'
import { toast } from 'sonner'
import { showToast } from './ToastNotification'

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}))

afterEach(() => {
  vi.clearAllMocks()
})

describe('showToast', () => {
  it('leaves placement to AppToaster instead of pinning top-right', () => {
    showToast.success('Alert created successfully')
    showToast.info('Refreshing alerts...')

    const successOptions = vi.mocked(toast.success).mock.calls[0]?.[1]
    const infoOptions = vi.mocked(toast.info).mock.calls[0]?.[1]

    expect(successOptions).not.toHaveProperty('position')
    expect(infoOptions).not.toHaveProperty('position')
  })
})
