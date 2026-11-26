import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('FixMySociety entry flow', () => {
  it('shows the resident sign-in screen and registration link', async () => {
    localStorage.clear();
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Create an account' })).toBeTruthy();
  });
});
