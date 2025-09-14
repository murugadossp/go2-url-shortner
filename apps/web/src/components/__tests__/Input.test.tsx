import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../ui/Input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" placeholder="Enter email" />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter email/i)).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<Input label="Email" error="Email is required" />);
    
    const input = screen.getByLabelText(/email/i);
    const errorMessage = screen.getByRole('alert');
    
    expect(input).toHaveClass('border-red-500');
    expect(errorMessage).toHaveTextContent('Email is required');
  });

  it('handles input changes', () => {
    const handleChange = jest.fn();
    render(<Input label="Email" onChange={handleChange} />);
    
    const input = screen.getByLabelText(/email/i);
    fireEvent.change(input, { target: { value: 'test@example.com' } });
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('supports different input types', () => {
    render(<Input type="password" label="Password" />);
    
    const input = screen.getByLabelText(/password/i);
    expect(input).toHaveAttribute('type', 'password');
  });

  it('can be disabled', () => {
    render(<Input label="Email" disabled />);
    
    const input = screen.getByLabelText(/email/i);
    expect(input).toBeDisabled();
    expect(input).toHaveClass('disabled:opacity-50');
  });

  it('applies custom className', () => {
    render(<Input label="Email" className="custom-input" />);
    
    const input = screen.getByLabelText(/email/i);
    expect(input).toHaveClass('custom-input');
  });
});