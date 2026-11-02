export function PageIntro({ title, description }: { title: string; description: string }) {
  // Reserve matching text rows so navigation stays still as the longer copy wraps.
  return <div className="mb-9">
    <h1 className="min-h-[2lh] text-[1.8rem] leading-tight font-bold tracking-tight min-[400px]:min-h-[1lh]">{title}</h1>
    <p className="mt-2 min-h-[4lh] text-lg leading-relaxed text-muted min-[400px]:min-h-[3lh] min-[640px]:min-h-[2lh] min-[1024px]:min-h-[1lh]">{description}</p>
  </div>;
}
