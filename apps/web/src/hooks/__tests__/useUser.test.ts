import { renderHook, act, waitFor } from '@testing-library/react';
import { useUser } from '../useUser';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';

// Mock dependencies
jest.mock('@/contexts/AuthContext');
jest.mock('@/lib/api');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseApiClient = useApiClient as jest.MockedFunction<typeof useApiClient>;

// Mock fetch for plan limits
global.fetch = jest.fn();

describe('useUser', () => {
  const mockUser = {
    uid: 'test-uid',
    email: 'test@example.com',
    displayName: 'Test User',
  };

  const mockProfile = {
    email: 'test@example.com',
    display_name: 'Test User',
    plan_type: 'free' as const,
    custom_codes_used: 2,
    custom_codes_remaining: 3,
    custom_codes_reset_date: '2024-02-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    is_admin: false,
  };

  const mockUsageStats = {
    total_links: 10,
    custom_code_links: 2,
    total_clicks: 150,
    plan_type: 'free' as const,
    custom_codes_used: 2,
    custom_codes_remaining: 3,
    custom_codes_reset_date: '2024-02-01T00:00:00Z',
  };

  const mockPlanLimits = {
    plans: {
      free: {
        custom_codes: 5,
        features: ['Basic URL shortening', 'QR codes', 'Basic analytics'],
      },
      paid: {
        custom_codes: 100,
        features: ['All free features', '100 custom codes per month', 'Advanced analytics'],
      },
    },
  };

  const mockApiClient = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApiClient.mockReturnValue(mockApiClient);
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPlanLimits),
    });
  });

  it('initializes with default state when no user', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    const { result } = renderHook(() => useUser());

    expect(result.current.profile).toBeNull();
    expect(result.current.usageStats).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isPaidUser).toBe(false);
  });

  it('fetches user data when user is authenticated', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get
      .mockResolvedValueOnce(mockProfile) // profile call
      .mockResolvedValueOnce(mockUsageStats); // usage stats call

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
      expect(result.current.usageStats).toEqual(mockUsageStats);
      expect(result.current.planLimits).toEqual(mockPlanLimits);
      expect(result.current.loading).toBe(false);
      expect(result.current.isAuthenticated).toBe(true);
    });

    expect(mockApiClient.get).toHaveBeenCalledWith('/api/users/profile');
    expect(mockApiClient.get).toHaveBeenCalledWith('/api/users/usage');
    expect(global.fetch).toHaveBeenCalledWith('/api/users/limits');
  });

  it('handles API errors gracefully', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.error).toBe('API Error');
      expect(result.current.loading).toBe(false);
    });
  });

  it('updates profile successfully', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);
    mockApiClient.put.mockResolvedValue({ message: 'Success' });

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
    });

    let updateResult: boolean;
    await act(async () => {
      updateResult = await result.current.updateProfile('New Name');
    });

    expect(updateResult!).toBe(true);
    expect(mockApiClient.put).toHaveBeenCalledWith('/api/users/profile', {
      display_name: 'New Name',
    });
  });

  it('upgrades plan successfully', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);
    mockApiClient.post.mockResolvedValue({ message: 'Success' });

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
    });

    let upgradeResult: boolean;
    await act(async () => {
      upgradeResult = await result.current.upgradePlan();
    });

    expect(upgradeResult!).toBe(true);
    expect(mockApiClient.post).toHaveBeenCalledWith('/api/users/upgrade', {
      plan_type: 'paid',
    });
  });

  it('calculates usage percentage correctly', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
    });

    // 2 used out of 5 total = 40%
    expect(result.current.getUsagePercentage()).toBe(40);
  });

  it('determines if user can create custom code', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
    });

    expect(result.current.canCreateCustomCode()).toBe(true); // 3 remaining

    // Test with no remaining codes
    const profileAtLimit = { ...mockProfile, custom_codes_remaining: 0 };
    mockApiClient.get.mockResolvedValue(profileAtLimit);

    await act(async () => {
      await result.current.refreshData();
    });

    expect(result.current.canCreateCustomCode()).toBe(false);
  });

  it('determines when to show upgrade prompt', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    // Test with 1 remaining (should show prompt)
    const profileNearLimit = { ...mockProfile, custom_codes_remaining: 1, custom_codes_used: 4 };
    mockApiClient.get.mockResolvedValue(profileNearLimit);

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(profileNearLimit);
    });

    expect(result.current.shouldShowUpgradePrompt()).toBe(true);

    // Test with paid plan (should not show prompt)
    const paidProfile = { ...mockProfile, plan_type: 'paid' as const };
    mockApiClient.get.mockResolvedValue(paidProfile);

    await act(async () => {
      await result.current.refreshData();
    });

    expect(result.current.shouldShowUpgradePrompt()).toBe(false);
  });

  it('identifies paid users correctly', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    const paidProfile = { ...mockProfile, plan_type: 'paid' as const };
    mockApiClient.get.mockResolvedValue(paidProfile);

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(paidProfile);
    });

    expect(result.current.isPaidUser).toBe(true);
  });

  it('formats reset date correctly', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
    });

    const formattedDate = result.current.formatResetDate(mockProfile.custom_codes_reset_date);
    expect(formattedDate).toBe('February 1, 2024');
  });

  it('handles empty reset date', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    const { result } = renderHook(() => useUser());

    expect(result.current.formatResetDate('')).toBe('');
    expect(result.current.formatResetDate(undefined)).toBe('');
  });

  it('refreshes data on demand', async () => {
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.profile).toEqual(mockProfile);
    });

    // Clear mock calls
    mockApiClient.get.mockClear();

    await act(async () => {
      await result.current.refreshData();
    });

    expect(mockApiClient.get).toHaveBeenCalledTimes(2); // profile and usage
  });

  it('clears data when user signs out', async () => {
    const { rerender } = renderHook(() => useUser());

    // Start with authenticated user
    mockUseAuth.mockReturnValue({
      user: mockUser as any,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    mockApiClient.get.mockResolvedValue(mockProfile);

    rerender();

    await waitFor(() => {
      expect(renderHook(() => useUser()).result.current.profile).toEqual(mockProfile);
    });

    // Sign out user
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: jest.fn(),
      signOut: jest.fn(),
      getIdToken: jest.fn(),
    });

    rerender();

    const { result } = renderHook(() => useUser());
    expect(result.current.profile).toBeNull();
    expect(result.current.usageStats).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});