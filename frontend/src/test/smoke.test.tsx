import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { App } from '../composition/App';

test('renders the NorthStar application', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'NorthStar Policy Desk' })).toBeVisible();
});
