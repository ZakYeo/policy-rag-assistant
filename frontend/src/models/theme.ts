import type { Theme, ThemePreferences } from '../contracts/theme';

const key = 'northstar-theme';
function storedTheme(): Theme | null {
  try {
    const value = localStorage.getItem(key);
    return value === 'light' || value === 'dark' ? value : null;
  } catch { return null; }
}
export function createThemePreferences(): ThemePreferences {
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  let override = storedTheme();
  const listeners = new Set<() => void>();
  const read = (): Theme => override ?? (media.matches ? 'dark' : 'light');
  const apply = () => {
    document.documentElement.dataset.theme = read();
    document.documentElement.style.colorScheme = read();
    listeners.forEach((listener) => listener());
  };
  const systemChanged = () => { if (!override) apply(); };
  const storageChanged = (event: StorageEvent) => {
    if (event.key === key || event.key === null) { override = storedTheme(); apply(); }
  };
  return {
    read,
    write(theme) {
      override = theme;
      try { localStorage.setItem(key, theme); } catch { /* In-memory override still works. */ }
      apply();
    },
    subscribe(listener) {
      if (listeners.size === 0) {
        media.addEventListener('change', systemChanged);
        window.addEventListener('storage', storageChanged);
      }
      listeners.add(listener);
      apply();
      return () => {
        listeners.delete(listener);
        if (listeners.size === 0) {
          media.removeEventListener('change', systemChanged);
          window.removeEventListener('storage', storageChanged);
        }
      };
    },
  };
}
