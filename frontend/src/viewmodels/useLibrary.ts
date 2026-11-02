import { useEffect, useRef, useState } from 'react';
import type { ChunkPage, LibraryClient, LibraryViewModel, ManagedPolicy, PolicyDetail, PolicyOperation } from '../contracts/library';

export function useLibrary(client: LibraryClient): LibraryViewModel {
  const [policies, setPolicies] = useState<ManagedPolicy[]>([]);
  const [detail, setDetail] = useState<PolicyDetail | null>(null);
  const [chunks, setChunks] = useState<ChunkPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<LibraryViewModel['tab']>('content');
  const selection = useRef(0);
  const [file, setFile] = useState<File | null>(null);
  const [operation, setOperation] = useState<PolicyOperation | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
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
    setLoading(true); setError(null); setDetail(null); setChunks(null); setTab('content'); setConfirmDelete(false);
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
  async function deletePolicy() {
    if (!detail || busy || !confirmDelete) return;
    setBusy(true); setError(null);
    try { await client.delete(detail.id, detail.version); ++selection.current; setDetail(null); setChunks(null); setConfirmDelete(false); await refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to delete policy.'); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    if (!operation || !['queued', 'running'].includes(operation.status)) return;
    const timer = setTimeout(() => {
      void client.operation(operation.id).then(async (next) => {
        setOperation(next);
        if (next.status === 'succeeded' || next.status === 'failed') {
          setBusy(false); await refresh(); await select(next.policy_id);
          if (next.error) setError(next.error);
        }
      }).catch((reason: unknown) => {
        setBusy(false); setOperation(null);
        setError(reason instanceof Error ? reason.message : 'Unable to check processing. Refresh policies.');
      });
    }, 700);
    return () => clearTimeout(timer);
  }, [operation, client]); // eslint-disable-line react-hooks/exhaustive-deps
  async function upload() {
    if (!file || busy) return;
    if (file.size > 20 * 1024 * 1024 || !file.size) { setError('Upload a non-empty file of at most 20 MiB.'); return; }
    setBusy(true); setError(null);
    try { setOperation(await client.upload(file)); setFile(null); await refresh(); }
    catch (reason) { setBusy(false); setError(reason instanceof Error ? reason.message : 'Unable to upload policy.'); }
  }
  async function retry() {
    if (!detail || busy) return;
    setBusy(true); setError(null);
    try { setOperation(await client.retry(detail.id, detail.version)); }
    catch (reason) { setBusy(false); setError(reason instanceof Error ? reason.message : 'Unable to retry processing.'); }
  }
  return { file, setFile, upload, retry, operation, confirmDelete, setConfirmDelete, deletePolicy, title, setTitle, rename, busy, policies, detail, chunks, loading, error, tab, refresh, select, setTab, loadChunks };
}
