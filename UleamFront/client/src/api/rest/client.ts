import { env, ensureEnvValue } from '@/config/env';
import { authStorage } from '@/lib/auth-storage';

export type RestMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RestRequestOptions {
  method?: RestMethod;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: RestRequestOptions['query']) {
  const base = ensureEnvValue('restBaseUrl').replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${base}${normalizedPath}`);

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
    const message = (data as any)?.message ?? res.statusText;
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
  const headers: Record<string, string> = {
    ...options.headers,
  };

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
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

export const restClient = {
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

export type PagedResult<T> = {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
};

export function isRestConfigured() {
  return Boolean(env.restBaseUrl);
}
