import { useSyncExternalStore } from 'react';
import type { ThemePreferences, ThemeViewModel } from '../contracts/theme';

export function useTheme(preferences: ThemePreferences): ThemeViewModel {
  const theme = useSyncExternalStore(preferences.subscribe, preferences.read);
  return { theme, toggle: () => preferences.write(theme === 'dark' ? 'light' : 'dark') };
}
