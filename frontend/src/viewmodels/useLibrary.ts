import { useEffect, useRef, useState } from 'react';
import { usePolicyOperation } from './usePolicyOperation';
import type { ChunkPage, LibraryClient, LibraryViewModel, ManagedPolicy, PolicyDetail, ChunkSettings, ChunkPreview } from '../contracts/library';

export function useLibrary(client: LibraryClient): LibraryViewModel {
  const [policies, setPolicies] = useState<ManagedPolicy[]>([]);
  const [detail, setDetail] = useState<PolicyDetail | null>(null);
  const [chunks, setChunks] = useState<ChunkPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<LibraryViewModel['tab']>('content');
  const selection = useRef(0);
  const [settings, setDraftSettings] = useState<ChunkSettings | null>(null);
  const [preview, setPreview] = useState<ChunkPreview | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [title, setTitle] = useState('');
  const [actionBusy, setBusy] = useState(false);
  const mounted = useRef(true);
  const processing = usePolicyOperation(client, async (next) => {
    if (!mounted.current) return;
    await refresh();
    if (!mounted.current) return;
    await select(next.policy_id);
    if (next.error) setError(next.error);
  });
  const busy = actionBusy || processing.pending;
  const operation = processing.operation;
  async function refresh() {
    setLoading(true); setError(null);
    try {
      const next = await client.list();
      if (!mounted.current) return;
      setPolicies(next);
      const pending = next.find((policy) => policy.status === 'processing' && policy.operation_id);
      if (pending?.operation_id && processing.trackedId.current !== pending.operation_id) {
        processing.track({ id: pending.operation_id, policy_id: pending.id, status: 'queued', stage: 'Resuming processing status', error: null });
      }
    }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load policies.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { mounted.current = true; void refresh(); return () => { mounted.current = false; ++selection.current; }; }, [client]); // eslint-disable-line react-hooks/exhaustive-deps
  async function select(id: string) {
    const request = ++selection.current;
    setLoading(true); setError(null); setDetail(null); setChunks(null); setPreview(null); setTab('content'); setConfirmDelete(false);
    try {
      const [next, page] = await Promise.all([client.detail(id), client.chunks(id, 0)]);
      if (request === selection.current) { setDetail(next); setTitle(next.title); setDraftSettings(next.settings); setChunks(page); }
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
  async function upload() {
    if (!file || busy) return;
    if (file.size > 20 * 1024 * 1024 || !file.size) { setError('Upload a non-empty file of at most 20 MiB.'); return; }
    setBusy(true); setError(null);
    try { processing.track(await client.upload(file)); setBusy(false); setFile(null); await refresh(); }
    catch (reason) { setBusy(false); setError(reason instanceof Error ? reason.message : 'Unable to upload policy.'); }
  }
  async function retry() {
    if (!detail || busy) return;
    setBusy(true); setError(null);
    try { processing.track(await client.retry(detail.id, detail.version)); setBusy(false); }
    catch (reason) { setBusy(false); setError(reason instanceof Error ? reason.message : 'Unable to retry processing.'); }
  }
  function setSettings(value: ChunkSettings) { setDraftSettings(value); setPreview(null); }
  async function previewChunks() {
    if (!detail || !settings || busy) return;
    setBusy(true); setError(null); setPreview(null);
    try { setPreview(await client.preview(detail.id, settings, detail.version)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to preview chunks.'); }
    finally { setBusy(false); }
  }
  async function loadPreview(offset: number) {
    if (!detail || !preview || busy) return;
    setBusy(true); setError(null);
    try { const chunks = await client.previewChunks(detail.id, preview.id, offset); setPreview({ ...preview, chunks }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load preview chunks.'); }
    finally { setBusy(false); }
  }
  async function applyPreview() {
    if (!detail || !preview || busy) return;
    setBusy(true); setError(null);
    try { processing.track(await client.apply(detail.id, preview.id, detail.version)); setBusy(false); }
    catch (reason) { setBusy(false); setPreview(null); setError(reason instanceof Error ? reason.message : 'Unable to apply chunking.'); }
  }
  return { connectionError: processing.connectionError, settings, setSettings, preview, previewChunks, loadPreview, applyPreview, file, setFile, upload, retry, operation, confirmDelete, setConfirmDelete, deletePolicy, title, setTitle, rename, busy, policies, detail, chunks, loading, error, tab, refresh, select, setTab, loadChunks };
}
