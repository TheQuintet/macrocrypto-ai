import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  dismissToastOnClosePointerDown,
  listenForToastClosePointer,
} from './toastClosePointer'

function pointerDown(target: EventTarget) {
  const event = new PointerEvent('pointerdown', {
    bubbles: true,
    cancelable: true,
    button: 0,
  })
  Object.defineProperty(event, 'target', { value: target })
  return event
}

describe('dismissToastOnClosePointerDown', () => {
  afterEach(() => {
    document.body.replaceChildren()
  })

  it('clicks the close button so the toast cannot capture the pointer', () => {
    const toast = document.createElement('li')
    toast.setAttribute('data-sonner-toast', '')
    const close = document.createElement('button')
    close.setAttribute('data-close-button', 'true')
    const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    close.append(icon)
    toast.append(close)
    document.body.append(toast)

    const closeClick = vi.fn()
    close.addEventListener('click', closeClick)

    const event = pointerDown(icon)
    dismissToastOnClosePointerDown(event)

    expect(event.defaultPrevented).toBe(true)
    expect(closeClick).toHaveBeenCalledTimes(1)
  })

  it('ignores pointerdowns that are not on a toast close button', () => {
    const button = document.createElement('button')
    const click = vi.fn()
    button.addEventListener('click', click)
    document.body.append(button)

    const event = pointerDown(button)
    dismissToastOnClosePointerDown(event)

    expect(event.defaultPrevented).toBe(false)
    expect(click).not.toHaveBeenCalled()
  })
})

describe('listenForToastClosePointer', () => {
  afterEach(() => {
    document.body.replaceChildren()
  })

  it('dismisses from a capturing pointerdown on the close control', () => {
    const toast = document.createElement('li')
    toast.setAttribute('data-sonner-toast', '')
    const close = document.createElement('button')
    close.setAttribute('data-close-button', 'true')
    toast.append(close)
    document.body.append(toast)

    const toastPointer = vi.fn()
    const closeClick = vi.fn()
    toast.addEventListener('pointerdown', toastPointer)
    close.addEventListener('click', closeClick)

    const stop = listenForToastClosePointer()
    close.dispatchEvent(
      new PointerEvent('pointerdown', {
        bubbles: true,
        cancelable: true,
        button: 0,
      }),
    )
    stop()

    expect(toastPointer).not.toHaveBeenCalled()
    expect(closeClick).toHaveBeenCalledTimes(1)
  })
})
