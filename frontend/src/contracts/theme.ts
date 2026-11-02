export type Theme = 'light' | 'dark';
export interface ThemePreferences {
  read(): Theme;
  write(theme: Theme): void;
  subscribe(listener: () => void): () => void;
}
export interface ThemeViewModel { theme: Theme; toggle(): void }
