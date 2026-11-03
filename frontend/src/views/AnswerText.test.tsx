import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { AnswerText } from './AnswerText';

test('renders paragraphs, emphasis, underline, filenames and lists', () => {
  const { container } = render(<AnswerText text={'**No.** See `policy.pdf`, **Page 2**.\n\nUse *approved* tools and <u>check first</u>.\n\n- Ask your manager\n- Read the policy'} />);
  expect(container.querySelectorAll('.answer-text > p')).toHaveLength(2);
  expect(screen.getByText('Page 2').tagName).toBe('STRONG');
  expect(screen.getByText('policy.pdf').tagName).toBe('CODE');
  expect(screen.getByText('approved').tagName).toBe('EM');
  expect(screen.getByText('check first').tagName).toBe('U');
  expect(screen.getAllByRole('listitem')).toHaveLength(2);
});

test('removes active HTML, attributes, images and links from model output', () => {
  const { container } = render(<AnswerText text={'<script>alert(1)</script><img src="https://example.com/track"><iframe src="https://example.com"></iframe>\n\n<u onclick="alert(1)" style="position:fixed" id="evil">Safe</u> [link](javascript:alert%281%29) ![image](https://example.com/track)'} />);
  expect(container.querySelector('script, img, iframe, a, [onclick], [style], #evil')).toBeNull();
  expect(screen.getByText('Safe').tagName).toBe('U');
  expect(container).not.toHaveTextContent('alert(1)');
});

test('supports incomplete streamed Markdown and the completed response', () => {
  const { rerender } = render(<AnswerText text={'See **Page'} />);
  expect(screen.getByText(/Page/)).toBeVisible();
  rerender(<AnswerText text={'See **Page 2**.\n\nUse `policy.pdf`.'} />);
  expect(screen.getByText('Page 2').tagName).toBe('STRONG');
  expect(screen.getByText('policy.pdf').tagName).toBe('CODE');
});

test('preserves literal policy extracts including Markdown and HTML', () => {
  const text = '<img src=x onerror="alert(1)"> **verbatim**';
  const { container } = render(<AnswerText text={text} extractive />);
  expect(container).toHaveTextContent(text);
  expect(container.querySelector('img, strong')).toBeNull();
});
