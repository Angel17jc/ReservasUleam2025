export const env = {
  restBaseUrl: import.meta.env.VITE_REST_BASE_URL?.trim() ?? "",
  graphqlUrl: import.meta.env.VITE_GRAPHQL_URL?.trim() ?? "",
  wsUrl: import.meta.env.VITE_WS_URL?.trim() ?? "",
};

export function ensureEnvValue(name: keyof typeof env): string {
  const value = env[name];
  if (!value) {
    console.warn(`[env] Falta la variable ${name}. Configura el .env local.`);
  }
  return value;
}
