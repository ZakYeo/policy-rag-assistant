import { useEffect, useRef, useState } from 'react';
import type { EvaluationClient, EvaluationMetadata, EvaluationRun, EvaluationViewModel } from '../contracts/evaluation';

export function useEvaluation(client: EvaluationClient): EvaluationViewModel {
  const [metadata, setMetadata] = useState<EvaluationMetadata | null>(null);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const startingRef = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const [meta, list] = await Promise.all([client.metadata(controller.signal), client.list(controller.signal)]);
        if (controller.signal.aborted) return;
        setMetadata(meta); setRuns(list);
        const id = selected || list[0]?.id;
        if (id && !selected) { setSelected(id); return; }
        const detail = id ? await client.get(id, controller.signal) : null;
        if (controller.signal.aborted) return;
        setRun(detail); setError(null); setLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Unable to load evaluations.'); setLoading(false);
      } finally {
        if (!controller.signal.aborted) timer = setTimeout(refresh, 3000);
      }
    }
    void refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [client, selected]);

  async function start() {
    if (startingRef.current) return;
    startingRef.current = true; setStarting(true); setError(null);
    try {
      const created = await client.start();
      if (mounted.current) { setRun(created); setRuns((list) => [created, ...list]); setSelected(created.id); }
    } catch (err) {
      if (mounted.current) setError(err instanceof Error ? err.message : 'Unable to start evaluation.');
    } finally {
      startingRef.current = false;
      if (mounted.current) setStarting(false);
    }
  }
  return { metadata, runs, run, selected, error, loading, starting,
    active: runs.some((item) => ['queued', 'running'].includes(item.status)),
    select(id) { setSelected(id); setRun(null); setLoading(true); }, start };
}
