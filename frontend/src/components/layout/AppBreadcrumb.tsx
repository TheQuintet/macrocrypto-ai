import { Link, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { navItemFromPathname, pageCopy, routes } from '@/constants/navigation'

/** App name plus the page you are on, so pages need no repeated title. */
export function AppBreadcrumb() {
  const { pathname } = useLocation()
  const currentPage = navItemFromPathname(pathname)

  return (
    <nav aria-label="Breadcrumb" className="min-w-0">
      <ol className="flex min-w-0 items-center gap-1.5">
        <li className="shrink-0">
          <Link
            to={routes.dashboard}
            className="font-mono text-sm font-medium tracking-tight text-muted-foreground transition-colors hover:text-foreground"
          >
            MacroCrypto&nbsp;AI
          </Link>
        </li>
        <li aria-hidden="true" className="shrink-0">
          <ChevronRight className="h-4 w-4 text-muted-foreground/60" />
        </li>
        <li className="min-w-0">
          <span aria-current="page" className="block truncate text-sm font-medium">
            {pageCopy[currentPage].title}
          </span>
        </li>
      </ol>
    </nav>
  )
}
