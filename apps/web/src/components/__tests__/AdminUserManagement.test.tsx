import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminUserManagement } from '../AdminUserManagement';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';
import { useToast } from '../ui/Toast';

// Mock dependencies
jest.mock('@/contexts/AuthContext');
jest.mock('@/lib/api');
jest.mock('../ui/Toast');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseApiClient = useApiClient as jest.MockedFunction<typeof useApiClient>;
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>;

describe('AdminUserManagement', () => {
  const mockApiClient = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  };

  const mockToast = {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  };

  const mockUsers = [
    {
      email: 'user1@example.com',
      display_name: 'User One',
      plan_type: 'free' as const,
      custom_codes_used: 2,
      custom_codes_remaining: 3,
      custom_codes_reset_date: '2024-02-15T10:00:00Z',
      created_at: '2024-01-01T10:00:00Z',
      is_admin: false,
    },
    {
      email: 'user2@example.com',
      display_name: 'User Two',
      plan_type: 'paid' as const,
      custom_codes_used: 15,
      custom_codes_remaining: 85,
      custom_codes_reset_date: '2024-02-20T10:00:00Z',
      created_at: '2024-01-05T10:00:00Z',
      is_admin: false,
    },
    {
      email: 'admin@example.com',
      display_name: 'Admin User',
      plan_type: 'paid' as const,
      custom_codes_used: 5,
      custom_codes_remaining: 95,
      custom_codes_reset_date: '2024-02-25T10:00:00Z',
      created_at: '2023-12-01T10:00:00Z',
      is_admin: true,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApiClient.mockReturnValue(mockApiClient);
    mockUseToast.mockReturnValue(mockToast);
  });

  describe('Access Control', () => {
    it('should show access denied for non-admin users', () => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'user123',
          email: 'user@example.com',
          customClaims: { admin: false },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      render(<AdminUserManagement />);

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText('You need administrator privileges to access this page.')).toBeInTheDocument();
    });

    it('should show user management for admin users', async () => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      mockApiClient.get.mockResolvedValue({ data: mockUsers });

      render(<AdminUserManagement />);

      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('Manage user accounts and permissions')).toBeInTheDocument();
    });
  });

  describe('User List Display', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });
    });

    it('should display loading state initially', () => {
      mockApiClient.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<AdminUserManagement />);

      expect(screen.getByText('Loading users...')).toBeInTheDocument();
    });

    it('should display users when loaded', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockUsers });

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
        expect(screen.getByText('User Two')).toBeInTheDocument();
        expect(screen.getByText('Admin User')).toBeInTheDocument();
      });

      // Check email addresses
      expect(screen.getByText('user1@example.com')).toBeInTheDocument();
      expect(screen.getByText('user2@example.com')).toBeInTheDocument();
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    it('should display user plan badges correctly', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockUsers });

      render(<AdminUserManagement />);

      await waitFor(() => {
        const freeBadges = screen.getAllByText('free');
        const paidBadges = screen.getAllByText('paid');
        
        expect(freeBadges).toHaveLength(1);
        expect(paidBadges).toHaveLength(2);
      });
    });

    it('should display admin shield icon for admin users', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockUsers });

      render(<AdminUserManagement />);

      await waitFor(() => {
        // Admin user should have shield icon
        const adminRow = screen.getByText('Admin User').closest('tr');
        expect(adminRow).toBeInTheDocument();
        // Shield icon should be present (we can't easily test for the icon itself in jsdom)
      });
    });

    it('should display usage statistics', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockUsers });

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('2 / 5')).toBeInTheDocument(); // User One usage
        expect(screen.getByText('15 / 100')).toBeInTheDocument(); // User Two usage
        expect(screen.getByText('5 / 100')).toBeInTheDocument(); // Admin usage
      });
    });
  });

  describe('Search Functionality', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      mockApiClient.get.mockResolvedValue({ data: mockUsers });
    });

    it('should filter users by email', async () => {
      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search users by email or name...');
      fireEvent.change(searchInput, { target: { value: 'user1@example.com' } });

      expect(screen.getByText('User One')).toBeInTheDocument();
      expect(screen.queryByText('User Two')).not.toBeInTheDocument();
      expect(screen.queryByText('Admin User')).not.toBeInTheDocument();
    });

    it('should filter users by display name', async () => {
      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User Two')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search users by email or name...');
      fireEvent.change(searchInput, { target: { value: 'User Two' } });

      expect(screen.queryByText('User One')).not.toBeInTheDocument();
      expect(screen.getByText('User Two')).toBeInTheDocument();
      expect(screen.queryByText('Admin User')).not.toBeInTheDocument();
    });

    it('should show no results message when search yields no matches', async () => {
      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search users by email or name...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      expect(screen.getByText('No users found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search terms.')).toBeInTheDocument();
    });
  });

  describe('Plan Management', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      mockApiClient.get.mockResolvedValue({ data: mockUsers });
    });

    it('should update user plan when button is clicked', async () => {
      mockApiClient.put.mockResolvedValue({});

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      const makePaidButton = screen.getByText('Make Paid');
      fireEvent.click(makePaidButton);

      await waitFor(() => {
        expect(mockApiClient.put).toHaveBeenCalledWith(
          '/api/users/admin/user1@example.com/plan',
          { plan_type: 'paid' }
        );
      });

      expect(mockToast.success).toHaveBeenCalledWith(
        'Plan updated',
        "User One's plan has been updated to paid."
      );
    });

    it('should handle plan update errors', async () => {
      mockApiClient.put.mockRejectedValue(new Error('API Error'));

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      const makePaidButton = screen.getByText('Make Paid');
      fireEvent.click(makePaidButton);

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          'Failed to update plan',
          'Please try again.'
        );
      });
    });

    it('should show loading state during plan update', async () => {
      mockApiClient.put.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      const makePaidButton = screen.getByText('Make Paid');
      fireEvent.click(makePaidButton);

      // Should show loading spinner (we can't easily test for the spinner itself)
      expect(makePaidButton).toBeDisabled();
    });
  });

  describe('Admin Status Management', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      mockApiClient.get.mockResolvedValue({ data: mockUsers });
    });

    it('should grant admin status when button is clicked', async () => {
      mockApiClient.put.mockResolvedValue({});

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      const makeAdminButton = screen.getByText('Make Admin');
      fireEvent.click(makeAdminButton);

      await waitFor(() => {
        expect(mockApiClient.put).toHaveBeenCalledWith(
          '/api/users/admin/user1@example.com/admin-status',
          { is_admin: true }
        );
      });

      expect(mockToast.success).toHaveBeenCalledWith(
        'Admin status granted',
        'User One is now an administrator.'
      );
    });

    it('should revoke admin status when button is clicked', async () => {
      mockApiClient.put.mockResolvedValue({});

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('Admin User')).toBeInTheDocument();
      });

      const revokeAdminButton = screen.getByText('Revoke Admin');
      fireEvent.click(revokeAdminButton);

      await waitFor(() => {
        expect(mockApiClient.put).toHaveBeenCalledWith(
          '/api/users/admin/admin@example.com/admin-status',
          { is_admin: false }
        );
      });

      expect(mockToast.success).toHaveBeenCalledWith(
        'Admin status revoked',
        'Admin User is no longer an administrator.'
      );
    });

    it('should disable admin toggle for current user', async () => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com', // Same as one of the users
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('Admin User')).toBeInTheDocument();
      });

      const revokeAdminButton = screen.getByText('Revoke Admin');
      expect(revokeAdminButton).toBeDisabled();
    });
  });

  describe('Summary Statistics', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      mockApiClient.get.mockResolvedValue({ data: mockUsers });
    });

    it('should display correct summary statistics', async () => {
      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument(); // Total users
      });

      // Check for paid users count
      const summarySection = screen.getByText('Total Users').closest('.grid');
      expect(summarySection).toHaveTextContent('2'); // Paid users
      expect(summarySection).toHaveTextContent('1'); // Administrators
      expect(summarySection).toHaveTextContent('22'); // Custom codes used (2+15+5)
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });
    });

    it('should handle API errors when loading users', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          'Failed to load users',
          'Please try again later.'
        );
      });
    });

    it('should show empty state when no users exist', async () => {
      mockApiClient.get.mockResolvedValue({ data: [] });

      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('No users found')).toBeInTheDocument();
        expect(screen.getByText('No users have signed up yet.')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: {
          uid: 'admin123',
          email: 'admin@example.com',
          customClaims: { admin: true },
        },
        loading: false,
        signIn: jest.fn(),
        signOut: jest.fn(),
      });

      mockApiClient.get.mockResolvedValue({ data: mockUsers });
    });

    it('should refresh data when refresh button is clicked', async () => {
      render(<AdminUserManagement />);

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Refresh'));

      expect(mockApiClient.get).toHaveBeenCalledTimes(2); // Initial load + refresh
    });
  });
});