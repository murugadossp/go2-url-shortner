import React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: string;
  label?: string;
  options: { value: string; label: string }[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, label, options, id, ...props }, ref) => {
    // Use a stable ID generation approach to avoid hydration mismatches
    const stableId = React.useId();
    const selectId = id || stableId;

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-semibold text-gray-800 mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            className={cn(
              'flex h-12 w-full rounded-xl border border-white/30 backdrop-blur-sm bg-white/50 px-4 py-3 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:bg-white/70 focus-visible:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 appearance-none pr-10 transition-all duration-300',
              error && 'border-red-500/50 focus-visible:ring-red-500 bg-red-50/30',
              className
            )}
            ref={ref}
            id={selectId}
            {...props}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-500 pointer-events-none" />
        </div>
        {error && (
          <p className="text-sm text-red-600 font-medium mt-2" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';