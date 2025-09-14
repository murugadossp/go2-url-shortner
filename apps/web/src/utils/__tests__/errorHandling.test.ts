/**
 * Tests for error handling utilities
 */

import {
  isAPIError,
  isValidationError,
  isRateLimitError,
  getErrorMessage,
  getFieldErrors,
  getRetryInfo,
  formatErrorForDisplay,
  retryWithBackoff
} from '../errorHandling';

describe('Error Type Guards', () => {
  test('isAPIError identifies API errors correctly', () => {
    const apiError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input'
      }
    };

    const nonApiError = {
      message: 'Regular error'
    };

    expect(isAPIError(apiError)).toBe(true);
    expect(isAPIError(nonApiError)).toBe(false);
    expect(isAPIError(null)).toBe(false);
    expect(isAPIError(undefined)).toBe(false);
  });

  test('isValidationError identifies validation errors correctly', () => {
    const validationError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        details: []
      }
    };

    const otherError = {
      error: {
        code: 'NOT_FOUND',
        message: 'Resource not found'
      }
    };

    expect(isValidationError(validationError)).toBe(true);
    expect(isValidationError(otherError)).toBe(false);
  });

  test('isRateLimitError identifies rate limit errors correctly', () => {
    const rateLimitError = {
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests',
        details: { retry_after: 60 }
      }
    };

    const otherError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input'
      }
    };

    expect(isRateLimitError(rateLimitError)).toBe(true);
    expect(isRateLimitError(otherError)).toBe(false);
  });
});

describe('Error Message Formatting', () => {
  test('getErrorMessage returns user-friendly messages for API errors', () => {
    const testCases = [
      {
        error: { error: { code: 'VALIDATION_ERROR', message: 'Invalid data' } },
        expected: 'Please check your input and try again.'
      },
      {
        error: { error: { code: 'SAFETY_VIOLATION', message: 'Malicious URL' } },
        expected: 'This URL cannot be shortened due to safety concerns.'
      },
      {
        error: { error: { code: 'RESOURCE_NOT_FOUND', message: 'Link not found' } },
        expected: 'The requested resource was not found.'
      },
      {
        error: { error: { code: 'RESOURCE_CONFLICT', message: 'Code exists' } },
        expected: 'This custom code is already taken. Please try another one.'
      },
      {
        error: { error: { code: 'AUTHENTICATION_ERROR', message: 'Not authenticated' } },
        expected: 'Please sign in to continue.'
      },
      {
        error: { error: { code: 'AUTHORIZATION_ERROR', message: 'No permission' } },
        expected: 'You do not have permission to perform this action.'
      },
      {
        error: { error: { code: 'RATE_LIMIT_EXCEEDED', message: 'Too many requests' } },
        expected: 'Too many requests. Please wait a moment and try again.'
      },
      {
        error: { error: { code: 'PLAN_LIMIT_EXCEEDED', message: 'Limit reached' } },
        expected: 'You have reached your plan limit. Please upgrade to continue.'
      },
      {
        error: { error: { code: 'EXTERNAL_SERVICE_ERROR', message: 'Service down' } },
        expected: 'External service is temporarily unavailable. Please try again later.'
      },
      {
        error: { error: { code: 'UNKNOWN_ERROR', message: 'Something went wrong' } },
        expected: 'Something went wrong'
      }
    ];

    testCases.forEach(({ error, expected }) => {
      expect(getErrorMessage(error)).toBe(expected);
    });
  });

  test('getErrorMessage handles network errors', () => {
    const networkError = new TypeError('Failed to fetch');
    expect(getErrorMessage(networkError)).toBe('Network error. Please check your connection and try again.');
  });

  test('getErrorMessage handles timeout errors', () => {
    const timeoutError = new Error('Request timeout');
    timeoutError.name = 'AbortError';
    expect(getErrorMessage(timeoutError)).toBe('Request timed out. Please try again.');
  });

  test('getErrorMessage provides fallback for unknown errors', () => {
    const unknownError = new Error('Something weird happened');
    expect(getErrorMessage(unknownError)).toBe('An unexpected error occurred. Please try again.');
  });
});

describe('Field Error Extraction', () => {
  test('getFieldErrors extracts validation field errors', () => {
    const validationError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        details: [
          {
            field: 'url',
            message: 'Invalid URL format',
            type: 'value_error'
          },
          {
            field: 'custom_code',
            message: 'Code already exists',
            type: 'value_error'
          }
        ]
      }
    };

    const fieldErrors = getFieldErrors(validationError);
    
    expect(fieldErrors).toEqual({
      url: 'Invalid URL format',
      custom_code: 'Code already exists'
    });
  });

  test('getFieldErrors returns empty object for non-validation errors', () => {
    const otherError = {
      error: {
        code: 'NOT_FOUND',
        message: 'Resource not found'
      }
    };

    expect(getFieldErrors(otherError)).toEqual({});
  });
});

describe('Retry Information', () => {
  test('getRetryInfo identifies retryable rate limit errors', () => {
    const rateLimitError = {
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests',
        details: { retry_after: 60 }
      }
    };

    const retryInfo = getRetryInfo(rateLimitError);
    
    expect(retryInfo.canRetry).toBe(true);
    expect(retryInfo.retryAfter).toBe(60);
  });

  test('getRetryInfo identifies retryable service errors', () => {
    const serviceError = {
      error: {
        code: 'EXTERNAL_SERVICE_ERROR',
        message: 'Service unavailable'
      }
    };

    const retryInfo = getRetryInfo(serviceError);
    
    expect(retryInfo.canRetry).toBe(true);
    expect(retryInfo.retryAfter).toBeUndefined();
  });

  test('getRetryInfo identifies non-retryable errors', () => {
    const validationError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input'
      }
    };

    const retryInfo = getRetryInfo(validationError);
    
    expect(retryInfo.canRetry).toBe(false);
  });
});

describe('Error Display Formatting', () => {
  test('formatErrorForDisplay combines all error information', () => {
    const validationError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        details: [
          {
            field: 'url',
            message: 'Invalid URL format',
            type: 'value_error'
          }
        ]
      }
    };

    const formatted = formatErrorForDisplay(validationError);
    
    expect(formatted.message).toBe('Please check your input and try again.');
    expect(formatted.fieldErrors).toEqual({ url: 'Invalid URL format' });
    expect(formatted.canRetry).toBe(false);
    expect(formatted.isValidationError).toBe(true);
    expect(formatted.isRateLimitError).toBe(false);
  });

  test('formatErrorForDisplay handles rate limit errors', () => {
    const rateLimitError = {
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests',
        details: { retry_after: 30 }
      }
    };

    const formatted = formatErrorForDisplay(rateLimitError);
    
    expect(formatted.canRetry).toBe(true);
    expect(formatted.retryAfter).toBe(30);
    expect(formatted.isRateLimitError).toBe(true);
  });
});

describe('Retry with Backoff', () => {
  test('retryWithBackoff succeeds on first attempt', async () => {
    const successFn = jest.fn().mockResolvedValue('success');
    
    const result = await retryWithBackoff(successFn, 3, 100);
    
    expect(result).toBe('success');
    expect(successFn).toHaveBeenCalledTimes(1);
  });

  test('retryWithBackoff retries on retryable errors', async () => {
    const retryableError = {
      error: {
        code: 'EXTERNAL_SERVICE_ERROR',
        message: 'Service unavailable'
      }
    };

    const failThenSucceed = jest.fn()
      .mockRejectedValueOnce(retryableError)
      .mockRejectedValueOnce(retryableError)
      .mockResolvedValue('success');
    
    const result = await retryWithBackoff(failThenSucceed, 3, 10);
    
    expect(result).toBe('success');
    expect(failThenSucceed).toHaveBeenCalledTimes(3);
  });

  test('retryWithBackoff does not retry on non-retryable errors', async () => {
    const nonRetryableError = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input'
      }
    };

    const alwaysFail = jest.fn().mockRejectedValue(nonRetryableError);
    
    await expect(retryWithBackoff(alwaysFail, 3, 10)).rejects.toEqual(nonRetryableError);
    expect(alwaysFail).toHaveBeenCalledTimes(1);
  });

  test('retryWithBackoff gives up after max retries', async () => {
    const retryableError = {
      error: {
        code: 'EXTERNAL_SERVICE_ERROR',
        message: 'Service unavailable'
      }
    };

    const alwaysFail = jest.fn().mockRejectedValue(retryableError);
    
    await expect(retryWithBackoff(alwaysFail, 2, 10)).rejects.toEqual(retryableError);
    expect(alwaysFail).toHaveBeenCalledTimes(3); // Initial + 2 retries
  });
});

describe('Error Logging', () => {
  let consoleSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleSpy = jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  test('logError logs error information', () => {
    const { logError } = require('../errorHandling');
    
    const error = new Error('Test error');
    logError(error, 'test context');
    
    expect(consoleSpy).toHaveBeenCalledWith(
      'Error logged:',
      expect.objectContaining({
        error: 'Error: Test error',
        context: 'test context',
        timestamp: expect.any(String),
        userAgent: expect.any(String),
        url: expect.any(String)
      })
    );
  });
});