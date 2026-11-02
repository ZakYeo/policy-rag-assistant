import type { ReactNode } from 'react';

export function Panel({ title, meta, children, id }: { title: string; meta?: string; children: ReactNode; id: string }) {
  return <section aria-labelledby={id} className="panel">
    <div className="mb-5 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 border-b border-line-subtle pb-4">
      <h2 id={id} className="text-lg font-bold text-ink">{title}</h2>
      {meta && <span className="text-sm text-muted">{meta}</span>}
    </div>
    {children}
  </section>;
}
