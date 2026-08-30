import type { ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  description?: string
  children?: ReactNode
}

/** Shared page title + supporting copy; optional actions on the right. */
export function PageHeader({ title, description, children }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex min-w-0 flex-col gap-1">
        <h1 className="text-pretty text-xl font-semibold tracking-tight sm:text-2xl">
          {title}
        </h1>
        {description ? (
          <p className="max-w-2xl text-pretty text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {children ? (
        <div className="flex w-full min-w-0 shrink-0 flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
          {children}
        </div>
      ) : null}
    </div>
  )
}
