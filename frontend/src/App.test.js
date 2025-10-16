import { render, screen } from '@testing-library/react';
import App from './App';

test('renders student dashboard title', () => {
  render(<App />);
  const titleElement = screen.getByText(/Student Dashboard/i);
  expect(titleElement).toBeInTheDocument();
});