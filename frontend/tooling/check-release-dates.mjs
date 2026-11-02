// Run before npm ci. Inspect all locked versions, including optional/transitive packages.
import { readFile, writeFile } from 'node:fs/promises';

const config = await readFile(new URL('../.npmrc', import.meta.url), 'utf8');
const configuredCutoff = config.match(/^before=(.+)$/m)?.[1];
if (!configuredCutoff) throw new Error('Missing npm release-date cutoff');
const cutoff = new Date(Math.min(Date.parse(configuredCutoff), Date.now() - 4 * 86400000));
const lock = JSON.parse(await readFile(new URL('../package-lock.json', import.meta.url), 'utf8'));
const versions = new Map();
for (const [path, entry] of Object.entries(lock.packages)) {
  if (!path) continue;
  if (!entry.version || (!entry.inBundle && !entry.resolved?.startsWith('https://registry.npmjs.org/'))) {
    throw new Error(`Cannot verify registry release for ${path}`);
  }
  const name = entry.name ?? path.split('node_modules/').at(-1);
  if (!versions.has(name)) versions.set(name, new Set());
  versions.get(name).add(entry.version);
}

const queue = [...versions.entries()];
const records = [];
const errors = [];
async function worker() {
  while (queue.length) {
    const [name, releases] = queue.shift();
    try {
      const response = await fetch(`https://registry.npmjs.org/${encodeURIComponent(name)}`, {
        signal: AbortSignal.timeout(30000),
      });
      if (!response.ok) throw new Error(`Registry HTTP ${response.status}`);
      const metadata = await response.json();
      for (const version of releases) {
        const publishedAt = metadata.time?.[version];
        if (!publishedAt || !Number.isFinite(Date.parse(publishedAt))) {
          throw new Error(`Missing publish timestamp for ${version}`);
        }
        if (Date.parse(publishedAt) > cutoff.getTime()) {
          throw new Error(`${version} was released ${publishedAt}, after ${cutoff.toISOString()}`);
        }
        records.push({ name, version, publishedAt });
      }
    } catch (error) {
      errors.push(`${name}: ${error.message}`);
    }
  }
}
await Promise.all(Array.from({ length: 8 }, worker));
if (errors.length) throw new Error(`Release-date checks failed:\n${errors.join('\n')}`);
records.sort((a, b) => a.name.localeCompare(b.name) || a.version.localeCompare(b.version));
const report = { cutoff: cutoff.toISOString(), packages: records };
if (process.argv.includes('--write')) {
  await writeFile(new URL('../dependency-publish-audit.json', import.meta.url), JSON.stringify(report, null, 2) + '\n');
}
console.log(`Verified ${records.length} locked package versions against npm publish timestamps; all released by ${cutoff.toISOString()}.`);
