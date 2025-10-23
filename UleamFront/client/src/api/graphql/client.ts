import { env, ensureEnvValue } from '@/config/env';
import { authStorage } from '@/lib/auth-storage';

interface GraphqlResponse<T> {
  data?: T;
  errors?: { message: string }[];
}

export async function graphqlRequest<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const url = ensureEnvValue('graphqlUrl');
  const token = authStorage.getToken();
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ query, variables }),
    credentials: 'include',
  });

  const json = (await res.json()) as GraphqlResponse<T>;
  if (!res.ok || json.errors?.length) {
    const message = json.errors?.[0]?.message ?? res.statusText;
    throw new Error(message);
  }

  return json.data as T;
}

export const graphqlClient = {
  query: graphqlRequest,
  mutate: graphqlRequest,
};

export function isGraphqlConfigured() {
  return Boolean(env.graphqlUrl);
}
