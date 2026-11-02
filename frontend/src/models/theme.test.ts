import { beforeEach, expect, test, vi } from 'vitest';
import { createThemePreferences } from './theme';

beforeEach(() => { localStorage.clear(); document.documentElement.removeAttribute('data-theme'); });

test('follows the system initially and persists explicit overrides', () => {
  const media = { matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() };
  vi.stubGlobal('matchMedia', vi.fn(() => media));
  const store = createThemePreferences();
  expect(store.read()).toBe('dark');
  const changed = vi.fn();
  const unsubscribe = store.subscribe(changed);
  store.write('light');
  expect(store.read()).toBe('light');
  expect(localStorage.getItem('northstar-theme')).toBe('light');
  expect(document.documentElement.dataset.theme).toBe('light');
  expect(changed).toHaveBeenCalled();
  expect(createThemePreferences().read()).toBe('light');
  unsubscribe();
  expect(media.removeEventListener).toHaveBeenCalled();
});

test('remains usable when preference storage is blocked', () => {
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
  const get = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  const set = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  const store = createThemePreferences();
  expect(store.read()).toBe('light');
  expect(() => store.write('dark')).not.toThrow();
  expect(store.read()).toBe('dark');
  get.mockRestore(); set.mockRestore();
});
