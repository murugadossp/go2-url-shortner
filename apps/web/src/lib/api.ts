import { useAuth } from '@/contexts/AuthContext';
import { logError, retryWithBackoff, isAPIError } from '@/utils/errorHandling';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface ApiRequestOptions extends RequestInit {
  requireAuth?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ApiData = any;

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: ApiRequestOptions = {}
  ): Promise<T> {
    const { requireAuth = false, ...fetchOptions } = options;
    
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    };

    // Add authentication header if required
    if (requireAuth) {
      // This will be handled by the hook that uses this client
      // The token will be passed in the headers
    }

    // Add timeout to prevent hanging requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { 
            error: { 
              code: 'PARSE_ERROR', 
              message: `HTTP ${response.status}: ${response.statusText}` 
            } 
          };
        }

        // Log error for debugging
        logError(errorData, `API request to ${endpoint}`);

        // Throw the structured error
        throw errorData;
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      // Handle network errors
      if (error && typeof error === 'object' && 'name' in error && error.name === 'AbortError') {
        const timeoutError = {
          error: {
            code: 'TIMEOUT_ERROR',
            message: 'Request timed out. Please try again.'
          }
        };
        logError(timeoutError, `Timeout on ${endpoint}`);
        throw timeoutError;
      }

      // Handle fetch errors (network issues)
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = {
          error: {
            code: 'NETWORK_ERROR',
            message: 'Network error. Please check your connection and try again.'
          }
        };
        logError(networkError, `Network error on ${endpoint}`);
        throw networkError;
      }

      // Re-throw API errors as-is
      if (isAPIError(error)) {
        throw error;
      }

      // Handle unexpected errors
      const unexpectedError = {
        error: {
          code: 'UNEXPECTED_ERROR',
          message: 'An unexpected error occurred. Please try again.'
        }
      };
      logError(error, `Unexpected error on ${endpoint}`);
      throw unexpectedError;
    }
  }

  async get<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    return retryWithBackoff(() => 
      this.makeRequest<T>(endpoint, { ...options, method: 'GET' })
    );
  }

  async post<T>(endpoint: string, data?: ApiData, options: ApiRequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: ApiData, options: ApiRequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Create API client instance
export const apiClient = new ApiClient(API_BASE_URL);

// Hook for authenticated API calls
export function useApiClient() {
  const { getIdToken } = useAuth();

  const makeAuthenticatedRequest = async <T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: ApiData
  ): Promise<T> => {
    console.log('🔐 API Client: Starting authenticated request...');
    console.log('🔐 Method:', method);
    console.log('🔐 Endpoint:', endpoint);
    console.log('🔐 Full URL:', `${API_BASE_URL}${endpoint}`);
    
    const token = await getIdToken();
    
    console.log('🔐 Auth token obtained:', token ? 'YES ✓' : 'NO ❌');
    if (token) {
      console.log('🔐 Token preview:', token.substring(0, 50) + '...');
    }
    
    // If no token is available, don't make the request
    if (!token) {
      console.error('❌ No auth token available');
      throw {
        error: {
          code: 'NO_AUTH_TOKEN',
          message: 'Please sign in to view your links'
        }
      };
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };

    const options: RequestInit = {
      method,
      headers,
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
      console.log('🔐 Request body:', JSON.stringify(data, null, 2));
    }

    console.log('🔐 Request headers:', headers);
    console.log('🌐 Making fetch request...');

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

      console.log('🌐 Response received');
      console.log('🌐 Status:', response.status, response.statusText);
      console.log('🌐 Headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        console.error('❌ Response not OK');
        let errorData;
        try {
          errorData = await response.json();
          console.error('❌ Error response body:', errorData);
        } catch {
          console.error('❌ Could not parse error response as JSON');
          errorData = { 
            error: { 
              code: 'PARSE_ERROR', 
              message: `HTTP ${response.status}: ${response.statusText}` 
            } 
          };
        }
        
        // Only log errors that aren't authentication related
        if (response.status !== 401) {
          logError(errorData, `Authenticated API request to ${endpoint}`);
        }
        
        throw errorData;
      }

      console.log('✅ Response OK, parsing JSON...');
      const result = await response.json();
      console.log('✅ Parsed response:', result);
      return result;
      
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('❌ Network error during fetch:', error);
        throw {
          error: {
            code: 'NETWORK_ERROR',
            message: 'Network error. Please check your connection and try again.'
          }
        };
      }
      console.error('❌ Request failed:', error);
      throw error;
    }
  };

  return {
    get: <T>(endpoint: string) => makeAuthenticatedRequest<T>('GET', endpoint),
    post: <T>(endpoint: string, data?: ApiData) => makeAuthenticatedRequest<T>('POST', endpoint, data),
    put: <T>(endpoint: string, data?: ApiData) => makeAuthenticatedRequest<T>('PUT', endpoint, data),
    delete: <T>(endpoint: string) => makeAuthenticatedRequest<T>('DELETE', endpoint),
  };
}
