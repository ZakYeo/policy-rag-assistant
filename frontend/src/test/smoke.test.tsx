import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { App } from '../composition/App';

test('renders the NorthStar application', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Ask about NorthStar policies' })).toBeVisible();
  expect(screen.getByRole('textbox', { name: 'Your question' })).toHaveValue('');
  expect(screen.getByRole('button', { name: 'Ask a question' })).toBeEnabled();
});
