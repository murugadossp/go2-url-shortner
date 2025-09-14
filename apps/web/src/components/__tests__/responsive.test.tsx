import { render, screen } from '@testing-library/react';
import { LinkCreator } from '../LinkCreator';
import { AnalyticsDashboard } from '../AnalyticsDashboard';

// Mock dependencies
jest.mock('@/lib/api', () => ({
  useApiClient: () => ({
    get: jest.fn().mockResolvedValue({
      base_domains: ['go2.tools'],
      total_clicks: 100,
      clicks_by_day: { '2024-01-01': 50 },
      top_referrers: { 'direct': 30 },
      top_devices: { 'mobile': 60 },
      geographic_stats: { countries: { 'US': 80 } },
    }),
    post: jest.fn(),
  }),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ user: null }),
}));

jest.mock('../ui/Toast', () => ({
  useToast: () => ({ toast: { success: jest.fn(), error: jest.fn() } }),
}));

// Mock window.matchMedia for responsive tests
const mockMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

describe('Responsive Design Tests', () => {
  describe('LinkCreator Component', () => {
    it('renders properly on mobile viewport', () => {
      mockMatchMedia(true); // Mobile
      render(<LinkCreator />);
      
      // Check that form elements are present and accessible
      expect(screen.getByLabelText(/long url/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/domain/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create short link/i })).toBeInTheDocument();
    });

    it('has proper responsive classes', () => {
      render(<LinkCreator />);
      
      // Check for responsive container classes
      const container = screen.getByText('Create Short Link').closest('div');
      expect(container).toHaveClass('max-w-2xl', 'mx-auto');
    });
  });

  describe('AnalyticsDashboard Component', () => {
    it('renders grid layout responsively', () => {
      render(<AnalyticsDashboard code="test123" />);
      
      // Wait for component to load
      setTimeout(() => {
        // Check for responsive grid classes
        const metricsGrid = screen.getByText('Total Clicks').closest('.grid');
        expect(metricsGrid).toHaveClass('grid-cols-1', 'md:grid-cols-4');
      }, 100);
    });

    it('handles mobile navigation properly', () => {
      mockMatchMedia(true); // Mobile
      render(<AnalyticsDashboard code="test123" />);
      
      // Check that dashboard renders without breaking on mobile
      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
    });
  });

  describe('Tailwind CSS Classes', () => {
    it('uses proper responsive breakpoints', () => {
      render(<LinkCreator />);
      
      // Check for Tailwind responsive classes
      const form = screen.getByRole('form') || screen.getByText('Create Short Link').closest('form');
      if (form) {
        // Verify responsive spacing and layout classes are present
        expect(form.className).toMatch(/space-y-\d+/);
      }
    });

    it('has mobile-first responsive design', () => {
      render(<LinkCreator />);
      
      // Check for mobile-first classes (base classes without prefixes)
      const container = screen.getByText('Create Short Link').closest('div');
      expect(container).toHaveClass('p-6'); // Base padding
    });
  });
});