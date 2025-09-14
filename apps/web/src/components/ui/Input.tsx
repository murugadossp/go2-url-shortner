import React from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error, label, id, ...props }, ref) => {
    // Use a stable ID generation approach to avoid hydration mismatches
    const stableId = React.useId();
    const inputId = id || stableId;

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-semibold text-gray-800 mb-2"
          >
            {label}
          </label>
        )}
        <input
          type={type}
          className={cn(
            'flex h-12 w-full rounded-xl border border-white/30 backdrop-blur-sm bg-white/50 px-4 py-3 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:bg-white/70 focus-visible:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-300',
            error && 'border-red-500/50 focus-visible:ring-red-500 bg-red-50/30',
            className
          )}
          ref={ref}
          id={inputId}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-600 font-medium mt-2" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';