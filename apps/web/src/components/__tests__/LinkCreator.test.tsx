import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LinkCreator } from '../LinkCreator';
import { useApiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api');
const mockApiClient = useApiClient as jest.MockedFunction<typeof useApiClient>;

// Mock the toast hook
jest.mock('../ui/Toast', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('LinkCreator', () => {
  const mockGet = jest.fn();
  const mockPost = jest.fn();

  beforeEach(() => {
    mockApiClient.mockReturnValue({
      get: mockGet,
      post: mockPost,
      put: jest.fn(),
      delete: jest.fn(),
    });

    // Mock domain config response
    mockGet.mockResolvedValue({
      base_domains: ['go2.video', 'go2.reviews', 'go2.tools'],
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders form fields correctly', async () => {
    render(<LinkCreator />);

    expect(screen.getByLabelText(/long url/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/domain/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/custom code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password protection/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/expiration date/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create short link/i })).toBeInTheDocument();
  });

  it('validates required URL field', async () => {
    const user = userEvent.setup();
    render(<LinkCreator />);

    const submitButton = screen.getByRole('button', { name: /create short link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/url is required/i)).toBeInTheDocument();
    });
  });

  it('validates URL format', async () => {
    const user = userEvent.setup();
    render(<LinkCreator />);

    const urlInput = screen.getByLabelText(/long url/i);
    await user.type(urlInput, 'invalid-url');

    const submitButton = screen.getByRole('button', { name: /create short link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid url/i)).toBeInTheDocument();
    });
  });

  it('suggests domain based on URL', async () => {
    const user = userEvent.setup();
    render(<LinkCreator />);

    const urlInput = screen.getByLabelText(/long url/i);
    await user.type(urlInput, 'https://youtube.com/watch?v=123');

    await waitFor(() => {
      const domainSelect = screen.getByLabelText(/domain/i) as HTMLSelectElement;
      expect(domainSelect.value).toBe('go2.video');
    });
  });

  it('checks custom code availability', async () => {
    const user = userEvent.setup();
    mockGet.mockImplementation((url) => {
      if (url.includes('check-availability')) {
        return Promise.resolve({ available: true, suggestions: [] });
      }
      return Promise.resolve({ base_domains: ['go2.video', 'go2.reviews', 'go2.tools'] });
    });

    render(<LinkCreator />);

    const customCodeInput = screen.getByLabelText(/custom code/i);
    await user.type(customCodeInput, 'my-code');

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('check-availability/my-code')
      );
    });
  });

  it('shows suggestions when custom code is taken', async () => {
    const user = userEvent.setup();
    mockGet.mockImplementation((url) => {
      if (url.includes('check-availability')) {
        return Promise.resolve({ 
          available: false, 
          suggestions: ['my-code-1', 'my-code-2'] 
        });
      }
      return Promise.resolve({ base_domains: ['go2.video', 'go2.reviews', 'go2.tools'] });
    });

    render(<LinkCreator />);

    const customCodeInput = screen.getByLabelText(/custom code/i);
    await user.type(customCodeInput, 'taken-code');

    await waitFor(() => {
      expect(screen.getByText(/this code is already taken/i)).toBeInTheDocument();
      expect(screen.getByText('my-code-1')).toBeInTheDocument();
      expect(screen.getByText('my-code-2')).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const mockOnLinkCreated = jest.fn();
    
    mockPost.mockResolvedValue({
      short_url: 'https://go2.tools/abc123',
      code: 'abc123',
      qr_url: 'https://api.example.com/qr/abc123',
      long_url: 'https://example.com',
      base_domain: 'go2.tools',
    });

    render(<LinkCreator onLinkCreated={mockOnLinkCreated} />);

    const urlInput = screen.getByLabelText(/long url/i);
    await user.type(urlInput, 'https://example.com');

    const submitButton = screen.getByRole('button', { name: /create short link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/api/links/shorten', {
        long_url: 'https://example.com',
        base_domain: 'go2.tools',
      });
      expect(mockOnLinkCreated).toHaveBeenCalled();
    });
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    
    // Make the API call hang
    mockPost.mockImplementation(() => new Promise(() => {}));

    render(<LinkCreator />);

    const urlInput = screen.getByLabelText(/long url/i);
    await user.type(urlInput, 'https://example.com');

    const submitButton = screen.getByRole('button', { name: /create short link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/creating link/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });
  });

  it('validates custom code format', async () => {
    const user = userEvent.setup();
    render(<LinkCreator />);

    const customCodeInput = screen.getByLabelText(/custom code/i);
    await user.type(customCodeInput, 'ab'); // Too short

    const submitButton = screen.getByRole('button', { name: /create short link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/custom code must be at least 3 characters/i)).toBeInTheDocument();
    });
  });

  it('validates password length', async () => {
    const user = userEvent.setup();
    render(<LinkCreator />);

    const passwordInput = screen.getByLabelText(/password protection/i);
    await user.type(passwordInput, '123'); // Too short

    const submitButton = screen.getByRole('button', { name: /create short link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/password must be at least 4 characters/i)).toBeInTheDocument();
    });
  });
});