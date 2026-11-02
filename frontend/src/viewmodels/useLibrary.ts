import { useEffect, useRef, useState } from 'react';
import type { ChunkPage, LibraryClient, LibraryViewModel, ManagedPolicy, PolicyDetail } from '../contracts/library';

export function useLibrary(client: LibraryClient): LibraryViewModel {
  const [policies, setPolicies] = useState<ManagedPolicy[]>([]);
  const [detail, setDetail] = useState<PolicyDetail | null>(null);
  const [chunks, setChunks] = useState<ChunkPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<LibraryViewModel['tab']>('content');
  const selection = useRef(0);
  const [title, setTitle] = useState('');
  const [busy, setBusy] = useState(false);
  async function refresh() {
    setLoading(true); setError(null);
    try { setPolicies(await client.list()); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load policies.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, [client]); // eslint-disable-line react-hooks/exhaustive-deps
  async function select(id: string) {
    const request = ++selection.current;
    setLoading(true); setError(null); setDetail(null); setChunks(null); setTab('content');
    try {
      const [next, page] = await Promise.all([client.detail(id), client.chunks(id, 0)]);
      if (request === selection.current) { setDetail(next); setTitle(next.title); setChunks(page); }
    } catch (reason) { if (request === selection.current) setError(reason instanceof Error ? reason.message : 'Unable to open policy.'); }
    finally { if (request === selection.current) setLoading(false); }
  }
  async function loadChunks(offset: number) {
    if (!detail) return;
    const request = selection.current;
    try { const page = await client.chunks(detail.id, offset); if (request === selection.current) setChunks(page); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load chunks.'); }
  }
  async function rename() {
    if (!detail || busy) return;
    setBusy(true); setError(null);
    try { await client.rename(detail.id, title, detail.version); await refresh(); await select(detail.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to rename policy.'); }
    finally { setBusy(false); }
  }
  return { title, setTitle, rename, busy, policies, detail, chunks, loading, error, tab, refresh, select, setTab, loadChunks };
}
