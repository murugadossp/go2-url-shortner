import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthButton } from '../AuthButton';
import { useAuth } from '@/contexts/AuthContext';

// Mock the useAuth hook
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock the Toast component
jest.mock('../ui/Toast', () => ({
  Toast: ({ message, type, onClose }: any) => (
    <div data-testid="toast" data-type={type} onClick={onClose}>
      {message}
    </div>
  ),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('AuthButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows loading spinner when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // LoadingSpinner has role="status"
  });

  it('shows sign in button when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    expect(screen.getByRole('button', { name: /sign in with google/i })).toBeInTheDocument();
  });

  it('shows sign out button when user is authenticated', () => {
    const mockUser = {
      uid: 'test-uid',
      email: 'test@example.com',
      displayName: 'Test User',
      photoURL: 'https://example.com/photo.jpg',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
  });

  it('shows user profile when showProfile is true', () => {
    const mockUser = {
      uid: 'test-uid',
      email: 'test@example.com',
      displayName: 'Test User',
      photoURL: 'https://example.com/photo.jpg',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton showProfile={true} />);
    
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Test User' })).toBeInTheDocument();
  });

  it('calls signInWithGoogle when sign in button is clicked', async () => {
    const mockSignIn = jest.fn().mockResolvedValue(undefined);
    
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: mockSignIn,
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signInButton = screen.getByRole('button', { name: /sign in with google/i });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledTimes(1);
    });
  });

  it('calls signOut when sign out button is clicked', async () => {
    const mockSignOut = jest.fn().mockResolvedValue(undefined);
    const mockUser = {
      uid: 'test-uid',
      email: 'test@example.com',
      displayName: 'Test User',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: mockSignOut,
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signOutButton = screen.getByRole('button', { name: /sign out/i });
    fireEvent.click(signOutButton);

    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledTimes(1);
    });
  });

  it('shows success toast on successful sign in', async () => {
    const mockSignIn = jest.fn().mockResolvedValue(undefined);
    
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: mockSignIn,
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signInButton = screen.getByRole('button', { name: /sign in with google/i });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
      expect(screen.getByTestId('toast')).toHaveAttribute('data-type', 'success');
      expect(screen.getByText('Successfully signed in!')).toBeInTheDocument();
    });
  });

  it('shows error toast on sign in failure', async () => {
    const mockSignIn = jest.fn().mockRejectedValue(new Error('Sign in failed'));
    
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: mockSignIn,
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signInButton = screen.getByRole('button', { name: /sign in with google/i });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
      expect(screen.getByTestId('toast')).toHaveAttribute('data-type', 'error');
      expect(screen.getByText('Failed to sign in. Please try again.')).toBeInTheDocument();
    });
  });

  it('shows loading state during sign in', async () => {
    const mockSignIn = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: mockSignIn,
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signInButton = screen.getByRole('button', { name: /sign in with google/i });
    fireEvent.click(signInButton);

    // Should show loading state
    expect(signInButton).toBeDisabled();
    expect(screen.getByRole('status')).toBeInTheDocument(); // LoadingSpinner

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledTimes(1);
    });
  });

  it('shows loading state during sign out', async () => {
    const mockSignOut = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    const mockUser = {
      uid: 'test-uid',
      email: 'test@example.com',
      displayName: 'Test User',
    };

    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: mockSignOut,
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signOutButton = screen.getByRole('button', { name: /sign out/i });
    fireEvent.click(signOutButton);

    // Should show loading state
    expect(signOutButton).toBeDisabled();
    expect(screen.getByRole('status')).toBeInTheDocument(); // LoadingSpinner

    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledTimes(1);
    });
  });

  it('dismisses toast when clicked', async () => {
    const mockSignIn = jest.fn().mockResolvedValue(undefined);
    
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: mockSignIn,
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    render(<AuthButton />);
    
    const signInButton = screen.getByRole('button', { name: /sign in with google/i });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast')).toBeInTheDocument();
    });

    // Click to dismiss toast
    fireEvent.click(screen.getByTestId('toast'));

    await waitFor(() => {
      expect(screen.queryByTestId('toast')).not.toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    const { container } = render(<AuthButton className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });
});