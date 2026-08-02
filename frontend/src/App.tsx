import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

function App() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  return (
    <main className="relative grid min-h-svh place-content-center gap-4 bg-background px-6 text-center text-foreground">
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="absolute top-4 right-4"
        aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
        onClick={() => setIsDark((dark) => !dark)}
      >
        {isDark ? <Sun /> : <Moon />}
      </Button>
      <h1 className="text-3xl font-bold tracking-tight">MacroCrypto AI</h1>
      <p className="text-muted-foreground">Frontend scaffold is ready.</p>
      <div>
        <Button type="button">Get started</Button>
      </div>
    </main>
  )
}

export default App
