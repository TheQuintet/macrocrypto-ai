import type { ReactNode } from 'react'

type PageIntroProps = {
  description?: string
  children?: ReactNode
}

/** Supporting copy plus optional actions; the page name lives in the breadcrumb. */
export function PageIntro({ description, children }: PageIntroProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      {description ? (
        <p className="min-w-0 max-w-2xl text-pretty text-sm text-muted-foreground">
          {description}
        </p>
      ) : null}
      {children ? (
        <div className="flex w-full min-w-0 shrink-0 flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
          {children}
        </div>
      ) : null}
    </div>
  )
}
