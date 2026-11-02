import type { ChunkStrategy, LibraryViewModel } from '../contracts/library';
import { ChunkList, fieldStyle, primaryButton, secondaryButton } from './LibraryComponents';

export function ChunkSettingsForm({ vm }: { vm: LibraryViewModel }) {
  if (!vm.detail || !vm.settings) return null;
  const settings = vm.settings;
  const availableHtml = ['html', 'htm'].includes(vm.detail.format);
  return <div>
    <p className="mb-5 text-sm leading-relaxed text-muted">Applied: {vm.detail.settings.strategy} · {vm.detail.settings.size} characters · {vm.detail.settings.overlap} overlap. Preview changes before updating search. The current version stays searchable until processing succeeds.</p>
    <form onSubmit={(event) => { event.preventDefault(); void vm.previewChunks(); }}>
      <fieldset disabled={vm.busy || vm.detail.status !== 'ready'} className="space-y-5 disabled:opacity-60">
        <legend className="sr-only">Chunking configuration</legend>
        <label className="block text-sm font-semibold">Strategy<select value={settings.strategy} className={fieldStyle} onChange={(event) => vm.setSettings({ ...settings, strategy: event.target.value as ChunkStrategy })}>
          <option value="characters">Character length</option><option value="sentences">Sentences / punctuation</option><option value="paragraphs">Paragraphs</option>{availableHtml && <option value="html">HTML headings / sections</option>}
        </select></label>
        <div className="grid gap-4 min-[640px]:grid-cols-2">
          <label className="text-sm font-semibold">Maximum chunk size (characters)<input type="number" min={100} max={20000} required value={Number.isNaN(settings.size) ? '' : settings.size} className={fieldStyle} onChange={(event) => vm.setSettings({ ...settings, size: event.target.valueAsNumber })} /></label>
          <label className="text-sm font-semibold">Overlap (characters)<input type="number" min={0} max={settings.size - 1} required value={Number.isNaN(settings.overlap) ? '' : settings.overlap} className={fieldStyle} onChange={(event) => vm.setSettings({ ...settings, overlap: event.target.valueAsNumber })} /></label>
        </div>
        {settings.strategy === 'html' && <label className="block text-sm font-semibold">Split at heading levels up to<select className={fieldStyle} value={settings.heading_depth} onChange={(event) => vm.setSettings({ ...settings, heading_depth: Number(event.target.value) })}>{[1, 2, 3, 4, 5, 6].map((depth) => <option key={depth} value={depth}>H{depth}</option>)}</select></label>}
        <p className="text-sm text-muted">Oversized sections split to fit the maximum. Overlap stays within each page or section. HTML chunks repeat heading context within the size limit.</p>
        <button type="submit" className={secondaryButton}>Preview chunks</button>
      </fieldset>
    </form>
    {vm.busy && !vm.operation && <p role="status" className="mt-4 text-sm text-muted">Preparing chunks…</p>}
    {vm.preview && <section className="mt-7 border-t border-line pt-5" aria-label="Chunk preview">
      <h3 className="mb-2 text-lg font-bold">Preview — not applied</h3>
      <p className="mb-4 text-sm text-muted">Applying will replace the searchable chunks for this policy.</p>
      <button className={`${primaryButton} mb-5`} disabled={vm.busy} onClick={() => void vm.applyPreview()}>Apply changes</button>
      <ChunkList page={vm.preview.chunks} load={vm.loadPreview} />
    </section>}
  </div>;
}
