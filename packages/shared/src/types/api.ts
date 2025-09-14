export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface SuccessResponse<T = any> {
  data: T;
  message?: string;
}

export type ApiResponse<T = any> = SuccessResponse<T> | ErrorResponse;