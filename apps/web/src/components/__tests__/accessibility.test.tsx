import { render, screen } from '@testing-library/react';
import { LinkCreator } from '../LinkCreator';
import { LinkDisplay } from '../LinkDisplay';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// Mock dependencies
jest.mock('@/lib/api', () => ({
  useApiClient: () => ({
    get: jest.fn().mockResolvedValue({ base_domains: ['go2.tools'] }),
    post: jest.fn(),
  }),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ user: null }),
}));

jest.mock('../ui/Toast', () => ({
  useToast: () => ({ toast: { success: jest.fn(), error: jest.fn() } }),
}));

describe('Accessibility Tests', () => {
  describe('Button Component', () => {
    it('has proper ARIA attributes', () => {
      render(<Button aria-label="Test button">Click me</Button>);
      const button = screen.getByRole('button', { name: /test button/i });
      expect(button).toBeInTheDocument();
    });

    it('is keyboard accessible', () => {
      render(<Button>Accessible Button</Button>);
      const button = screen.getByRole('button');
      expect(button).not.toHaveAttribute('tabindex', '-1');
    });
  });

  describe('Input Component', () => {
    it('has proper label association', () => {
      render(<Input label="Email Address" />);
      const input = screen.getByLabelText(/email address/i);
      expect(input).toBeInTheDocument();
    });

    it('shows error with proper ARIA attributes', () => {
      render(<Input label="Email" error="Email is required" />);
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveTextContent('Email is required');
    });
  });

  describe('LinkCreator Component', () => {
    it('has proper form structure', () => {
      render(<LinkCreator />);
      
      // Check for form elements
      expect(screen.getByLabelText(/long url/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/domain/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create short link/i })).toBeInTheDocument();
    });

    it('has descriptive help text', () => {
      render(<LinkCreator />);
      
      // Check for help text
      expect(screen.getByText(/enter the url you want to shorten/i)).toBeInTheDocument();
      expect(screen.getByText(/choose a contextual domain/i)).toBeInTheDocument();
    });
  });

  describe('LinkDisplay Component', () => {
    const mockLink = {
      short_url: 'https://go2.tools/abc123',
      code: 'abc123',
      qr_url: 'https://api.example.com/qr/abc123',
      long_url: 'https://example.com',
      base_domain: 'go2.tools' as const,
    };

    it('has proper link accessibility', () => {
      render(<LinkDisplay link={mockLink} />);
      
      // Check for accessible links
      const shortLink = screen.getByRole('link', { name: /https:\/\/go2\.tools\/abc123/i });
      expect(shortLink).toHaveAttribute('target', '_blank');
      expect(shortLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('has proper button labels', () => {
      render(<LinkDisplay link={mockLink} />);
      
      expect(screen.getByRole('button', { name: /copy to clipboard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /show qr code/i })).toBeInTheDocument();
    });
  });
});