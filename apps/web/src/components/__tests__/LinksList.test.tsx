import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LinksList } from '../LinksList';
import { useUser } from '@/hooks/useUser';
import { apiClient } from '@/lib/api';

// Mock dependencies
jest.mock('@/hooks/useUser');
jest.mock('@/lib/api');

const mockUseUser = useUser as jest.MockedFunction<typeof useUser>;
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

const mockLinks = [
  {
    code: 'abc123',
    long_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    base_domain: 'go2.video',
    short_url: 'https://go2.video/abc123',
    created_at: '2024-01-01T00:00:00Z',
    clicks: 42,
    disabled: false,
    expires_at: null,
    is_custom_code: false,
  },
  {
    code: 'custom123',
    long_url: 'https://github.com/microsoft/playwright',
    base_domain: 'go2.tools',
    short_url: 'https://go2.tools/custom123',
    created_at: '2024-01-02T00:00:00Z',
    clicks: 15,
    disabled: false,
    expires_at: '2024-12-31T23:59:59Z',
    is_custom_code: true,
  },
];

describe('LinksList', () => {
  beforeEach(() => {
    mockUseUser.mockReturnValue({
      user: {
        uid: 'test-user',
        email: 'test@example.com',
        displayName: 'Test User',
      },
      loading: false,
    });

    mockApiClient.get.mockResolvedValue({
      data: mockLinks,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders links list correctly', async () => {
    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
      expect(screen.getByText('custom123')).toBeInTheDocument();
    });

    expect(screen.getByText('42 clicks')).toBeInTheDocument();
    expect(screen.getByText('15 clicks')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search links/i);
    await user.type(searchInput, 'youtube');

    // Should filter to show only YouTube link
    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
      expect(screen.queryByText('custom123')).not.toBeInTheDocument();
    });
  });

  it('handles sort functionality', async () => {
    const user = userEvent.setup();
    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
    });

    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, 'clicks-desc');

    // Should sort by clicks descending (abc123 first with 42 clicks)
    const linkElements = screen.getAllByTestId(/^link-item-/);
    expect(linkElements[0]).toHaveTextContent('abc123');
    expect(linkElements[1]).toHaveTextContent('custom123');
  });

  it('handles filter functionality', async () => {
    const user = userEvent.setup();
    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
    });

    // Filter by custom codes only
    const customCodeFilter = screen.getByLabelText(/custom codes only/i);
    await user.click(customCodeFilter);

    await waitFor(() => {
      expect(screen.queryByText('abc123')).not.toBeInTheDocument();
      expect(screen.getByText('custom123')).toBeInTheDocument();
    });
  });

  it('displays pagination controls', async () => {
    // Mock large dataset
    const manyLinks = Array.from({ length: 25 }, (_, i) => ({
      ...mockLinks[0],
      code: `link${i}`,
      short_url: `https://go2.video/link${i}`,
    }));

    mockApiClient.get.mockResolvedValue({
      data: manyLinks,
    });

    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('1 of 3')).toBeInTheDocument(); // Assuming 10 per page
    });

    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /previous page/i })).toBeDisabled();
  });

  it('handles copy link functionality', async () => {
    const user = userEvent.setup();
    
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined),
      },
    });

    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
    });

    const copyButton = screen.getAllByLabelText(/copy link/i)[0];
    await user.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://go2.video/abc123');
    
    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/copied to clipboard/i)).toBeInTheDocument();
    });
  });

  it('handles link deletion', async () => {
    const user = userEvent.setup();
    mockApiClient.delete.mockResolvedValue({ data: { success: true } });

    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
    });

    const deleteButton = screen.getAllByLabelText(/delete link/i)[0];
    await user.click(deleteButton);

    // Should show confirmation dialog
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();

    const confirmButton = screen.getByRole('button', { name: /delete/i });
    await user.click(confirmButton);

    expect(mockApiClient.delete).toHaveBeenCalledWith('/api/links/abc123');

    // Should remove link from list
    await waitFor(() => {
      expect(screen.queryByText('abc123')).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no links', async () => {
    mockApiClient.get.mockResolvedValue({
      data: [],
    });

    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText(/no links found/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/create your first link/i)).toBeInTheDocument();
  });

  it('handles loading state', () => {
    mockApiClient.get.mockReturnValue(new Promise(() => {})); // Never resolves

    render(<LinksList />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    mockApiClient.get.mockRejectedValue(new Error('Failed to fetch links'));

    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load links/i)).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('shows expiration indicators', async () => {
    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('custom123')).toBeInTheDocument();
    });

    // Should show expiration date for link with expires_at
    expect(screen.getByText(/expires/i)).toBeInTheDocument();
    expect(screen.getByText(/2024-12-31/)).toBeInTheDocument();
  });

  it('handles bulk operations', async () => {
    const user = userEvent.setup();
    mockApiClient.put.mockResolvedValue({ data: { success: true } });

    render(<LinksList />);

    await waitFor(() => {
      expect(screen.getByText('abc123')).toBeInTheDocument();
    });

    // Select multiple links
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[0]); // Select first link
    await user.click(checkboxes[1]); // Select second link

    // Bulk actions should be available
    const bulkActionsButton = screen.getByRole('button', { name: /bulk actions/i });
    expect(bulkActionsButton).toBeEnabled();

    await user.click(bulkActionsButton);
    
    const disableOption = screen.getByRole('menuitem', { name: /disable selected/i });
    await user.click(disableOption);

    expect(mockApiClient.put).toHaveBeenCalledWith('/api/links/bulk', {
      action: 'disable',
      codes: ['abc123', 'custom123'],
    });
  });
});