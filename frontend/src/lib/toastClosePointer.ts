const CLOSE_BUTTON_SELECTOR = '[data-sonner-toast] [data-close-button]'

/**
 * Sonner captures pointer on the toast card, which swallows clicks on its
 * close control. Stop that capture and dismiss via the button's own handler.
 */
export function dismissToastOnClosePointerDown(event: Event) {
  if (!(event instanceof PointerEvent) || event.button !== 0) return

  const target = event.target
  if (!(target instanceof Element)) return

  const close = target.closest(CLOSE_BUTTON_SELECTOR)
  if (!(close instanceof HTMLElement)) return

  event.preventDefault()
  event.stopPropagation()
  close.click()
}

export function listenForToastClosePointer() {
  document.addEventListener('pointerdown', dismissToastOnClosePointerDown, true)
  return () => {
    document.removeEventListener(
      'pointerdown',
      dismissToastOnClosePointerDown,
      true,
    )
  }
}
