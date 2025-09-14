import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnalyticsDashboard } from '../AnalyticsDashboard';
import { apiClient } from '@/lib/api';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  Legend: () => <div data-testid="legend" />,
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

const mockAnalyticsData = {
  total_clicks: 156,
  clicks_by_day: [
    { date: '2024-01-01', clicks: 25 },
    { date: '2024-01-02', clicks: 32 },
    { date: '2024-01-03', clicks: 28 },
    { date: '2024-01-04', clicks: 35 },
    { date: '2024-01-05', clicks: 36 },
  ],
  top_referrers: [
    { referrer: 'google.com', clicks: 45 },
    { referrer: 'twitter.com', clicks: 32 },
    { referrer: 'direct', clicks: 28 },
    { referrer: 'facebook.com', clicks: 25 },
  ],
  top_devices: [
    { device: 'desktop', clicks: 89 },
    { device: 'mobile', clicks: 52 },
    { device: 'tablet', clicks: 15 },
  ],
  geographic_data: [
    { country: 'United States', country_code: 'US', clicks: 78 },
    { country: 'Canada', country_code: 'CA', clicks: 34 },
    { country: 'United Kingdom', country_code: 'GB', clicks: 28 },
    { country: 'Germany', country_code: 'DE', clicks: 16 },
  ],
  last_clicked: '2024-01-05T14:30:00Z',
};

describe('AnalyticsDashboard', () => {
  beforeEach(() => {
    mockApiClient.get.mockResolvedValue({
      data: mockAnalyticsData,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders analytics data correctly', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('156')).toBeInTheDocument(); // Total clicks
    });

    expect(screen.getByText(/total clicks/i)).toBeInTheDocument();
    expect(screen.getByText(/last clicked/i)).toBeInTheDocument();
  });

  it('displays clicks over time chart', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('displays referrers breakdown', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('google.com')).toBeInTheDocument();
    });

    expect(screen.getByText('45')).toBeInTheDocument(); // Google clicks
    expect(screen.getByText('twitter.com')).toBeInTheDocument();
    expect(screen.getByText('32')).toBeInTheDocument(); // Twitter clicks
  });

  it('displays device breakdown chart', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });

    expect(screen.getByText('desktop')).toBeInTheDocument();
    expect(screen.getByText('mobile')).toBeInTheDocument();
    expect(screen.getByText('tablet')).toBeInTheDocument();
  });

  it('displays geographic data', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('United States')).toBeInTheDocument();
    });

    expect(screen.getByText('78')).toBeInTheDocument(); // US clicks
    expect(screen.getByText('Canada')).toBeInTheDocument();
    expect(screen.getByText('34')).toBeInTheDocument(); // Canada clicks
  });

  it('handles time period selection', async () => {
    const user = userEvent.setup();
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('156')).toBeInTheDocument();
    });

    // Change time period
    const periodSelect = screen.getByLabelText(/time period/i);
    await user.selectOptions(periodSelect, '30');

    expect(mockApiClient.get).toHaveBeenCalledWith('/api/stats/test123?period=30');
  });

  it('handles export functionality', async () => {
    const user = userEvent.setup();
    
    // Mock blob and URL creation
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = jest.fn();
    
    // Mock download response
    mockApiClient.get.mockImplementation((url) => {
      if (url.includes('export')) {
        return Promise.resolve({
          data: 'date,clicks\n2024-01-01,25\n2024-01-02,32',
          headers: {
            'content-type': 'text/csv',
          },
        });
      }
      return Promise.resolve({ data: mockAnalyticsData });
    });

    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('156')).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /export csv/i });
    await user.click(exportButton);

    expect(mockApiClient.get).toHaveBeenCalledWith('/api/stats/test123/export?format=csv');
  });

  it('shows empty state for no data', async () => {
    mockApiClient.get.mockResolvedValue({
      data: {
        total_clicks: 0,
        clicks_by_day: [],
        top_referrers: [],
        top_devices: [],
        geographic_data: [],
        last_clicked: null,
      },
    });

    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument(); // Total clicks
    });

    expect(screen.getByText(/no clicks yet/i)).toBeInTheDocument();
    expect(screen.getByText(/share your link/i)).toBeInTheDocument();
  });

  it('handles loading state', () => {
    mockApiClient.get.mockReturnValue(new Promise(() => {})); // Never resolves

    render(<AnalyticsDashboard code="test123" />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    mockApiClient.get.mockRejectedValue(new Error('Failed to fetch analytics'));

    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load analytics/i)).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('formats dates correctly', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText(/jan 5, 2024/i)).toBeInTheDocument(); // Last clicked date
    });
  });

  it('calculates percentages correctly', async () => {
    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('57.1%')).toBeInTheDocument(); // Desktop percentage (89/156)
    });

    expect(screen.getByText('33.3%')).toBeInTheDocument(); // Mobile percentage (52/156)
  });

  it('handles real-time updates', async () => {
    const { rerender } = render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('156')).toBeInTheDocument();
    });

    // Simulate new data
    mockApiClient.get.mockResolvedValue({
      data: {
        ...mockAnalyticsData,
        total_clicks: 160,
      },
    });

    rerender(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByText('160')).toBeInTheDocument();
    });
  });

  it('is responsive on mobile', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(<AnalyticsDashboard code="test123" />);

    await waitFor(() => {
      expect(screen.getByTestId('mobile-layout')).toBeInTheDocument();
    });

    // Charts should stack vertically on mobile
    const chartsContainer = screen.getByTestId('charts-container');
    expect(chartsContainer).toHaveClass('flex-col');
  });
});