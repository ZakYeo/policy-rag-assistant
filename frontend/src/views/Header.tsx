import type { ThemeViewModel } from '../contracts/theme';

export function Header({ theme, page = "/", navigate }: { theme: ThemeViewModel; page?: string; navigate?(path: string): void }) {
  return <header className="border-b border-line bg-card">
    <div className="page-width flex min-h-20 flex-wrap items-center justify-between gap-4 py-5">
      <div className="flex min-w-0 items-center gap-3">
        <svg viewBox="0 0 24 24" className="size-6 shrink-0 text-ink" aria-hidden="true"><path fill="currentColor" d="M12 1 14 9 22 12 14 15 12 23 10 15 2 12 10 9Z" /></svg>
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0">
          <strong className="text-2xl font-bold tracking-tight">NorthStar</strong>
          <span className="text-muted" aria-hidden="true">/</span>
          <span className="text-base text-muted">Policy Desk</span>
        </div>
      </div>
      <nav aria-label="Main navigation" className="order-3 flex w-full flex-wrap gap-x-4 gap-y-2 text-sm font-semibold min-[960px]:order-none min-[960px]:w-auto">
        {[["/", "Ask policies"], ["/policies", "Manage policies"], ["/evaluations", "RAG evaluation"]].map(([href, label]) => <a key={href} href={href} aria-current={page === href ? 'page' : undefined} className={`border-b-2 py-1 ${page === href ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-ink'}`} onClick={(event) => { if (navigate && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); navigate(href); } }}>{label}</a>)}
      </nav>
      <div className="flex shrink-0 items-center gap-4">
        <p className="hidden text-sm text-muted min-[1200px]:block">Internal policy guidance for employees</p>
        <button type="button" onClick={theme.toggle} aria-label={`Switch to ${theme.theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme.theme === 'dark' ? 'light' : 'dark'} mode`}
          className="flex size-10 items-center justify-center rounded border border-line text-ink hover:bg-inset">
          {theme.theme === 'dark'
            ? <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 1v3m0 16v3M1 12h3m16 0h3M4.2 4.2l2.1 2.1m11.4 11.4 2.1 2.1m0-15.6-2.1 2.1M6.3 17.7l-2.1 2.1" /></svg>
            : <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M20.5 14.5A9 9 0 0 1 9.5 3.5a9 9 0 1 0 11 11Z" /></svg>}
        </button>
      </div>
    </div>
  </header>;
}
