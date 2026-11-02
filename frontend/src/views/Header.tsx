export function Header() {
  return <header className="border-b border-line bg-card">
    <div className="page-width flex min-h-20 items-center justify-between gap-4 py-5">
      <div className="flex min-w-0 items-center gap-3">
        <svg viewBox="0 0 24 24" className="size-6 shrink-0 text-ink" aria-hidden="true"><path fill="currentColor" d="M12 1 14 9 22 12 14 15 12 23 10 15 2 12 10 9Z" /></svg>
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0">
          <strong className="text-2xl font-bold tracking-tight">NorthStar</strong>
          <span className="text-muted" aria-hidden="true">/</span>
          <span className="text-base text-muted">Policy Desk</span>
        </div>
      </div>
      <p className="hidden text-sm text-muted min-[768px]:block">Internal policy guidance for employees</p>
    </div>
  </header>;
}
