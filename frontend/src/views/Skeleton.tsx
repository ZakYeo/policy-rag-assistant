export function Skeleton({ rows = 3 }: { rows?: number }) {
  return <div className="space-y-3" aria-hidden="true">
    {Array.from({ length: rows }, (_, index) => <div key={index} data-testid="skeleton"
      className={`skeleton h-4 rounded ${index === rows - 1 ? 'w-2/3' : 'w-full'}`} />)}
  </div>;
}
