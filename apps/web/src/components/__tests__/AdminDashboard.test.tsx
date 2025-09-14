import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminDashboard } from '../AdminDashboard';
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

describe('AdminDashboard', () => {
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

  const mockOnTabChange = jest.fn();

  const mockSystemStats = {
    users: {
      total: 100,
      free: 80,
      paid: 20,
      admin: 3,
      recent_signups: 15,
    },
    links: {
      total: 500,
      custom_codes: 75,
      disabled: 10,
      recent_created: 50,
    },
    engagement: {
      total_clicks: 10000,
      avg_clicks_per_link: 20.0,
    },
    last_updated: '2024-01-15T10:00:00Z',
  };

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

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText('You need administrator privileges to access this page.')).toBeInTheDocument();
    });

    it('should show dashboard for admin users', async () => {
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

      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      expect(screen.getByText('System administration and monitoring')).toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
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

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      expect(screen.getByText('Loading statistics...')).toBeInTheDocument();
    });

    it('should display system statistics when loaded', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument(); // Total users
        expect(screen.getByText('500')).toBeInTheDocument(); // Total links
        expect(screen.getByText('10000')).toBeInTheDocument(); // Total clicks
        expect(screen.getByText('10')).toBeInTheDocument(); // Disabled links
      });
    });

    it('should display user breakdown correctly', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText('Free Plan Users')).toBeInTheDocument();
        expect(screen.getByText('Paid Plan Users')).toBeInTheDocument();
        expect(screen.getByText('Admin Users')).toBeInTheDocument();
      });

      // Check specific values
      const userBreakdownSection = screen.getByText('User Breakdown').closest('div');
      expect(userBreakdownSection).toHaveTextContent('80'); // Free users
      expect(userBreakdownSection).toHaveTextContent('20'); // Paid users
      expect(userBreakdownSection).toHaveTextContent('3'); // Admin users
    });

    it('should display link breakdown correctly', async () => {
      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText('Link Breakdown')).toBeInTheDocument();
      });

      const linkBreakdownSection = screen.getByText('Link Breakdown').closest('div');
      expect(linkBreakdownSection).toHaveTextContent('75'); // Custom codes
      expect(linkBreakdownSection).toHaveTextContent('425'); // Auto-generated (500-75)
      expect(linkBreakdownSection).toHaveTextContent('10'); // Disabled
    });
  });

  describe('Navigation', () => {
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

      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });
    });

    it('should render navigation tabs', async () => {
      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Users')).toBeInTheDocument();
        expect(screen.getByText('Links')).toBeInTheDocument();
        expect(screen.getByText('Audit Log')).toBeInTheDocument();
        expect(screen.getByText('Configuration')).toBeInTheDocument();
      });
    });

    it('should highlight active tab', async () => {
      render(<AdminDashboard activeTab="users" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        const usersTab = screen.getByText('Users').closest('button');
        expect(usersTab).toHaveClass('border-blue-500', 'text-blue-600');
      });
    });

    it('should call onTabChange when tab is clicked', async () => {
      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        const usersTab = screen.getByText('Users');
        fireEvent.click(usersTab);
      });

      expect(mockOnTabChange).toHaveBeenCalledWith('users');
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

    it('should handle API errors gracefully', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          'Failed to load statistics',
          'Please try again later.'
        );
      });

      expect(screen.getByText('Failed to load statistics')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('should allow retry after error', async () => {
      mockApiClient.get
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce({ data: mockSystemStats });

      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument(); // Stats loaded
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

      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });
    });

    it('should refresh data when refresh button is clicked', async () => {
      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Refresh'));

      expect(mockApiClient.get).toHaveBeenCalledTimes(2); // Initial load + refresh
    });

    it('should show last updated timestamp', async () => {
      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
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

      mockApiClient.get.mockResolvedValue({ data: mockSystemStats });
    });

    it('should have responsive grid classes', async () => {
      render(<AdminDashboard activeTab="overview" onTabChange={mockOnTabChange} />);

      await waitFor(() => {
        const statsGrid = screen.getByText('Total Users').closest('.grid');
        expect(statsGrid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4');
      });
    });
  });
});