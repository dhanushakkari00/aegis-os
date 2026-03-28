import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatInterface } from '../chat-interface';

// Mock the next/navigation globally
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

// Mock matchMedia to prevent Jest/Vitest UI component errors
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock the API library globally
vi.mock('@/lib/api', () => ({
  default: {
    createCase: vi.fn().mockResolvedValue({
      id: "abc-123",
      detected_case_type: "medical",
      urgency_level: "critical",
      confidence: 0.95,
      assistant_response: "Help is on the way."
    }),
    getNearbyResources: vi.fn().mockResolvedValue({
      places: [],
      static_map_url: "http://mock-map-url"
    })
  }
}));

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial welcome state', () => {
    render(<ChatInterface />);
    expect(screen.getByPlaceholderText(/Describe the emergency situation/i)).toBeInTheDocument();
  });

  it('allows user to type and send a message, updating the UI optimistically', async () => {
    render(<ChatInterface />);
    
    // Find input and submit button
    const input = screen.getByPlaceholderText(/Describe the emergency situation/i);
    // Fire event
    fireEvent.change(input, { target: { value: 'There is a fire in the building!' } });
    expect(input).toHaveValue('There is a fire in the building!');
    
    // If testing the standard generic form submit:
    fireEvent.click(screen.getByRole('button', { name: /Send message/i })); // The SVG button
    
    // Check optimistic update
    await waitFor(() => {
      expect(screen.getByText('There is a fire in the building!')).toBeInTheDocument();
    });
  });
});
