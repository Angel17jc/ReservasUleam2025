import { env } from '@/config/env';
import { authStorage } from '@/lib/auth-storage';
import type { RestMethod, RestRequestOptions } from './client';

const API_PREFIX = '/api/v1';

function ensurePaymentBaseUrl() {
  const base = env.paymentBaseUrl?.replace(/\/$/, '');
  if (!base) {
    throw new Error('Configura VITE_PAYMENT_BASE_URL para consumir /api/v1/payments');
  }
  return base;
}

function buildUrl(path: string, query?: RestRequestOptions['query']) {
  const base = ensurePaymentBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const withPrefix = normalizedPath.startsWith(API_PREFIX) ? normalizedPath : `${API_PREFIX}${normalizedPath}`;
  const url = new URL(`${base}${withPrefix}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}

async function handleResponse<T>(res: Response): Promise<T> {
  const contentType = res.headers.get('content-type');
  const hasJson = Boolean(contentType && contentType.includes('application/json'));
  const data = hasJson ? await res.json() : undefined;

  if (!res.ok) {
    const message = (data as any)?.detail || (data as any)?.message || res.statusText;
    const error = new Error(message);
    (error as any).status = res.status;
    (error as any).body = data;
    throw error;
  }

  return data as T;
}

async function request<T>(path: string, options: RestRequestOptions = {}) {
  const method = options.method ?? 'GET';
  const token = authStorage.getToken();
  const headers: Record<string, string> = { ...options.headers };

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    // Añadir token en query para compatibilidad con middleware que acepta query cuando falta el header
    options.query = { ...(options.query ?? {}), token };
  }

  const res = await fetch(buildUrl(path, options.query), {
    method,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
    credentials: 'include',
  });

  return handleResponse<T>(res);
}

export const paymentClient = {
  request,
  get: <T>(path: string, options?: Omit<RestRequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<RestRequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RestRequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RestRequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Omit<RestRequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
};

export function isPaymentApiConfigured() {
  return Boolean(env.paymentBaseUrl);
}
