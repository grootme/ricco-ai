/**
 * API Client with SOLID Principles
 * 
 * Features:
 * - Retry logic with exponential backoff
 * - Request/Response caching
 * - Error handling with typed errors
 * - Request interceptors for auth
 * - Response interceptors for error handling
 */

// =============================================================================
// TYPES
// =============================================================================

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retryPolicy?: RetryPolicy;
  cacheConfig?: CacheConfig;
}

export interface RetryPolicy {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  retryableStatuses: number[];
}

export interface CacheConfig {
  enabled: boolean;
  ttl: number; // Time to live in milliseconds
  maxSize: number;
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean>;
  cache?: boolean;
  timeout?: number;
  signal?: AbortSignal;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
  timestamp: string;
  path?: string;
}

// =============================================================================
// DEFAULT CONFIGURATION
// =============================================================================

const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxRetries: 3,
  baseDelay: 100,
  maxDelay: 5000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

const DEFAULT_CACHE_CONFIG: CacheConfig = {
  enabled: true,
  ttl: 60000, // 1 minute
  maxSize: 100,
};

// =============================================================================
// API CLIENT
// =============================================================================

export class ApiClient {
  private baseURL: string;
  private timeout: number;
  private retryPolicy: RetryPolicy;
  private cache: Map<string, CacheEntry<unknown>>;
  private cacheConfig: CacheConfig;
  private requestInterceptors: Array<(headers: Headers) => Headers> = [];
  private responseInterceptors: Array<(response: Response) => void> = [];

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL;
    this.timeout = config.timeout ?? 30000;
    this.retryPolicy = config.retryPolicy ?? DEFAULT_RETRY_POLICY;
    this.cacheConfig = config.cacheConfig ?? DEFAULT_CACHE_CONFIG;
    this.cache = new Map();
  }

  // -------------------------------------------------------------------------
  // INTERCEPTORS
  // -------------------------------------------------------------------------

  addRequestInterceptor(interceptor: (headers: Headers) => Headers): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: (response: Response) => void): void {
    this.responseInterceptors.push(interceptor);
  }

  // -------------------------------------------------------------------------
  // HTTP METHODS
  // -------------------------------------------------------------------------

  async get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, undefined, options);
  }

  async post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, body, options);
  }

  async put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, body, options);
  }

  async patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PATCH', path, body, options);
  }

  async delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, undefined, options);
  }

  // -------------------------------------------------------------------------
  // CORE REQUEST METHOD
  // -------------------------------------------------------------------------

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const cacheKey = this.getCacheKey(method, path, options);

    // Check cache for GET requests
    if (method === 'GET' && options?.cache !== false) {
      const cached = this.getFromCache<T>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    // Build URL with query params
    const url = this.buildUrl(path, options?.params);

    // Execute with retry
    return this.executeWithRetry(async () => {
      const headers = this.buildHeaders(options?.headers);
      
      // Apply request interceptors
      const finalHeaders = this.requestInterceptors.reduce(
        (h, interceptor) => interceptor(h),
        headers
      );

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), options?.timeout ?? this.timeout);

      try {
        const response = await fetch(url, {
          method,
          headers: finalHeaders,
          body: body ? JSON.stringify(body) : undefined,
          signal: options?.signal ?? controller.signal,
        });

        clearTimeout(timeoutId);

        // Apply response interceptors
        this.responseInterceptors.forEach(interceptor => interceptor(response));

        if (!response.ok) {
          throw await this.createApiError(response);
        }

        const data = await response.json();

        // Cache successful GET responses
        if (method === 'GET' && options?.cache !== false) {
          this.setCache(cacheKey, data);
        }

        return data as T;
      } catch (error) {
        clearTimeout(timeoutId);
        throw error;
      }
    });
  }

  // -------------------------------------------------------------------------
  // HELPER METHODS
  // -------------------------------------------------------------------------

  private buildUrl(path: string, params?: Record<string, string | number | boolean>): string {
    const url = new URL(`${this.baseURL}${path}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });
    }
    
    return url.toString();
  }

  private buildHeaders(customHeaders?: Record<string, string>): Headers {
    const headers = new Headers({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    });

    if (customHeaders) {
      Object.entries(customHeaders).forEach(([key, value]) => {
        headers.set(key, value);
      });
    }

    return headers;
  }

  private getCacheKey(method: string, path: string, options?: RequestOptions): string {
    const params = options?.params ? JSON.stringify(options.params) : '';
    return `${method}:${path}:${params}`;
  }

  private getFromCache<T>(key: string): T | null {
    if (!this.cacheConfig.enabled) {
      return null;
    }

    const entry = this.cache.get(key) as CacheEntry<T> | undefined;
    if (!entry) {
      return null;
    }

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  private setCache<T>(key: string, data: T): void {
    if (!this.cacheConfig.enabled) {
      return;
    }

    // Enforce max size
    if (this.cache.size >= this.cacheConfig.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) {
        this.cache.delete(oldestKey);
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: this.cacheConfig.ttl,
    });
  }

  private async executeWithRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error | null = null;
    let attempt = 0;

    while (attempt < this.retryPolicy.maxRetries) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        attempt++;

        // Check if we should retry
        if (!this.shouldRetry(error, attempt)) {
          throw error;
        }

        // Wait before retrying
        await this.delay(this.calculateDelay(attempt));
      }
    }

    throw lastError;
  }

  private shouldRetry(error: unknown, attempt: number): boolean {
    if (attempt >= this.retryPolicy.maxRetries) {
      return false;
    }

    // Network errors should be retried
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return true;
    }

    // Check for retryable status codes
    if (error instanceof ApiErrorClass) {
      return this.retryPolicy.retryableStatuses.includes(error.status);
    }

    return false;
  }

  private calculateDelay(attempt: number): number {
    const delay = this.retryPolicy.baseDelay * Math.pow(2, attempt);
    return Math.min(delay, this.retryPolicy.maxDelay);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async createApiError(response: Response): Promise<ApiErrorClass> {
    let detail = '';
    try {
      const json = await response.json();
      detail = json.detail || json.message || '';
    } catch {
      detail = response.statusText;
    }

    return new ApiErrorClass({
      status: response.status,
      message: response.statusText,
      detail,
      timestamp: new Date().toISOString(),
    });
  }

  // -------------------------------------------------------------------------
  // CACHE MANAGEMENT
  // -------------------------------------------------------------------------

  clearCache(): void {
    this.cache.clear();
  }

  invalidateCache(pattern?: string): void {
    if (!pattern) {
      this.clearCache();
      return;
    }

    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

// =============================================================================
// API ERROR CLASS
// =============================================================================

class ApiErrorClass extends Error implements ApiError {
  status: number;
  detail?: string;
  timestamp: string;
  path?: string;

  constructor(data: ApiError) {
    super(data.message);
    this.name = 'ApiError';
    this.status = data.status;
    this.detail = data.detail;
    this.timestamp = data.timestamp;
    this.path = data.path;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isUnauthorized(): boolean {
    return this.status === 401;
  }

  isForbidden(): boolean {
    return this.status === 403;
  }

  isValidationError(): boolean {
    return this.status === 422;
  }

  isServerError(): boolean {
    return this.status >= 500;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = new ApiClient({
  baseURL: API_BASE_URL,
  timeout: 30000,
  retryPolicy: DEFAULT_RETRY_POLICY,
  cacheConfig: DEFAULT_CACHE_CONFIG,
});

// Add auth interceptor
if (typeof window !== 'undefined') {
  apiClient.addRequestInterceptor((headers) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  });
}

export { ApiErrorClass as ApiError };
