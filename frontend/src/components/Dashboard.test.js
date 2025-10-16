import { render, screen } from '@testing-library/react';
import Dashboard from './Dashboard';

test('renders upcoming assignments card', () => {
  render(<Dashboard />);
  const cardTitleElement = screen.getByText(/تکالیف پیش‌رو/i);
  expect(cardTitleElement).toBeInTheDocument();
});