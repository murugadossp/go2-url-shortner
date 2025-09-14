/**
 * Error handling utilities for the frontend application
 */

export interface APIError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface ValidationError {
  error: {
    code: 'VALIDATION_ERROR';
    message: string;
    details: Array<{
      field: string;
      message: string;
      type: string;
      input?: any;
    }>;
  };
}

export interface RateLimitError {
  error: {
    code: 'RATE_LIMIT_EXCEEDED';
    message: string;
    details: {
      retry_after?: number;
    };
  };
}

// Error type guards
export const isAPIError = (error: any): error is APIError => {
  return !!(error && typeof error === 'object' && 'error' in error && 
         error.error && typeof error.error === 'object' && 'code' in error.error);
};

export const isValidationError = (error: any): error is ValidationError => {
  return isAPIError(error) && error.error.code === 'VALIDATION_ERROR';
};

export const isRateLimitError = (error: any): error is RateLimitError => {
  return isAPIError(error) && error.error.code === 'RATE_LIMIT_EXCEEDED';
};

// User-friendly error messages
export const getErrorMessage = (error: any): string => {
  // Handle API errors
  if (isAPIError(error)) {
    switch (error.error.code) {
      case 'VALIDATION_ERROR':
        return 'Please check your input and try again.';
      case 'SAFETY_VIOLATION':
        return 'This URL cannot be shortened due to safety concerns.';
      case 'RESOURCE_NOT_FOUND':
        return 'The requested resource was not found.';
      case 'RESOURCE_CONFLICT':
        return 'This custom code is already taken. Please try another one.';
      case 'AUTHENTICATION_ERROR':
        return 'Please sign in to continue.';
      case 'AUTHORIZATION_ERROR':
        return 'You do not have permission to perform this action.';
      case 'RATE_LIMIT_EXCEEDED':
        return 'Too many requests. Please wait a moment and try again.';
      case 'PLAN_LIMIT_EXCEEDED':
        return 'You have reached your plan limit. Please upgrade to continue.';
      case 'EXTERNAL_SERVICE_ERROR':
        return 'External service is temporarily unavailable. Please try again later.';
      default:
        return error.error.message || 'An unexpected error occurred.';
    }
  }

  // Handle network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return 'Network error. Please check your connection and try again.';
  }

  // Handle timeout errors
  if (error.name === 'AbortError' || error.message?.includes('timeout')) {
    return 'Request timed out. Please try again.';
  }

  // Default fallback
  return 'An unexpected error occurred. Please try again.';
};

// Get validation error messages for specific fields
export const getFieldErrors = (error: any): Record<string, string> => {
  if (!isValidationError(error)) {
    return {};
  }

  const fieldErrors: Record<string, string> = {};
  
  for (const detail of error.error.details) {
    fieldErrors[detail.field] = detail.message;
  }

  return fieldErrors;
};

// Get retry information for rate limit errors
export const getRetryInfo = (error: any): { canRetry: boolean; retryAfter?: number } => {
  if (isRateLimitError(error)) {
    return {
      canRetry: true,
      retryAfter: error.error.details.retry_after
    };
  }

  // Check for other retryable errors
  const retryableCodes = [
    'EXTERNAL_SERVICE_ERROR',
    'INTERNAL_SERVER_ERROR',
    'BAD_GATEWAY',
    'SERVICE_UNAVAILABLE'
  ];

  if (isAPIError(error) && retryableCodes.includes(error.error.code)) {
    return { canRetry: true };
  }

  return { canRetry: false };
};

// Format error for display in UI components
export const formatErrorForDisplay = (error: any) => {
  const message = getErrorMessage(error);
  const fieldErrors = getFieldErrors(error);
  const retryInfo = getRetryInfo(error);

  return {
    message,
    fieldErrors,
    canRetry: retryInfo.canRetry,
    retryAfter: retryInfo.retryAfter,
    isValidationError: isValidationError(error),
    isRateLimitError: isRateLimitError(error)
  };
};

// Error logging utility
export const logError = (error: any, context?: string) => {
  const errorInfo = {
    error: error.toString(),
    stack: error.stack,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href
  };

  console.error('Error logged:', errorInfo);

  // In production, send to error tracking service
  if (process.env.NODE_ENV === 'production') {
    // TODO: Send to error tracking service (Sentry, LogRocket, etc.)
    try {
      // Example: Sentry.captureException(error, { extra: errorInfo });
    } catch (loggingError) {
      console.error('Failed to log error to external service:', loggingError);
    }
  }
};

// Retry utility with exponential backoff
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: any;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on certain error types
      if (isAPIError(error)) {
        const nonRetryableCodes = [
          'VALIDATION_ERROR',
          'AUTHENTICATION_ERROR',
          'AUTHORIZATION_ERROR',
          'RESOURCE_NOT_FOUND',
          'SAFETY_VIOLATION'
        ];

        if (nonRetryableCodes.includes(error.error.code)) {
          throw error;
        }
      }

      // Don't retry on the last attempt
      if (attempt === maxRetries) {
        break;
      }

      // Calculate delay with exponential backoff and jitter
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};

// Global error handler for unhandled promise rejections
export const setupGlobalErrorHandling = () => {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    logError(event.reason, 'unhandledrejection');
    
    // Prevent the default browser behavior (logging to console)
    event.preventDefault();
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    logError(event.error || event.message, 'global');
  });
};