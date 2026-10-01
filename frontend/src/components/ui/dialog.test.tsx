import { cleanup } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import {
  clickDialogButton,
  clickOverlay,
  expectDialogClosed,
  expectDialogFocused,
  expectFocused,
  openDialog,
  pressEscape,
  pressTab,
  renderDialog,
} from './dialog.testHelpers'

describe('Dialog accessibility', () => {
  afterEach(() => {
    cleanup()
  })

  it('is named by its title and described by its description', async () => {
    renderDialog()

    const dialog = await openDialog()

    expect(dialog).toHaveAccessibleName('Alert settings')
    expect(dialog).toHaveAccessibleDescription('Choose when to be notified.')
  })

  it('points at no description when it has none', async () => {
    renderDialog({ withDescription: false })

    const dialog = await openDialog()

    expect(dialog).not.toHaveAttribute('aria-describedby')
  })

  it('moves focus into the dialog when it opens', async () => {
    renderDialog()

    await openDialog()

    expectDialogFocused()
  })

  it('keeps Tab inside the dialog, wrapping both ways', async () => {
    renderDialog()
    await openDialog()

    await pressTab()
    expectFocused('First')
    await pressTab()
    expectFocused('Close')
    await pressTab()
    expectFocused('First')

    await pressTab(true)
    expectFocused('Close')
  })

  it('holds focus on the dialog when there is nothing to tab to', async () => {
    renderDialog({ withButtons: false })
    await openDialog()

    await pressTab()

    expectDialogFocused()
  })

  it('returns focus to the trigger when closed from inside', async () => {
    renderDialog()
    await openDialog()

    await clickDialogButton('Close')

    expectDialogClosed()
    expectFocused('Open')
  })

  it('still closes on Escape, returning focus', async () => {
    renderDialog()
    await openDialog()

    await pressEscape()

    expectDialogClosed()
    expectFocused('Open')
  })

  it('still closes on an overlay click', async () => {
    renderDialog()
    await openDialog()

    await clickOverlay()

    expectDialogClosed()
  })
})
