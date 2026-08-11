import { useEffect, useState } from 'react'
import type { Theme } from '@/types/theme'

const THEME_STORAGE_KEY = 'macrocrypto-theme'
const DEFAULT_THEME: Theme = 'dark'

function applyDocumentTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

function readStoredTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') {
      return stored
    }
  } catch {
    // Ignore storage access errors (private mode, blocked storage, etc.)
  }

  return DEFAULT_THEME
}

function persistTheme(theme: Theme) {
  applyDocumentTheme(theme)

  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // Ignore storage access errors (private mode, blocked storage, etc.)
  }
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => readStoredTheme())
  const isDark = theme === 'dark'

  useEffect(() => {
    applyDocumentTheme(theme)
  }, [theme])

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== THEME_STORAGE_KEY) {
        return
      }

      const nextTheme = event.newValue
      if (nextTheme !== 'light' && nextTheme !== 'dark') {
        return
      }

      applyDocumentTheme(nextTheme)
      setTheme(nextTheme)
    }

    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const toggleTheme = () => {
    const nextTheme: Theme = theme === 'dark' ? 'light' : 'dark'
    persistTheme(nextTheme)
    setTheme(nextTheme)
  }

  return { theme, isDark, toggleTheme }
}
