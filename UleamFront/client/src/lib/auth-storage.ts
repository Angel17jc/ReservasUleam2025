const TOKEN_KEY = 'uleam_token';
const USER_KEY = 'uleam_user';

type StoredUser = {
  id: string;
  nombre: string;
  email: string;
  role: 'user' | 'admin';
  tipoUsuarioNombre?: string;
  tipoUsuarioId?: number;
};

function normalizeUser(value: any): StoredUser | null {
  if (!value) return null;
  if (typeof value === 'string') {
    try {
      value = JSON.parse(value);
    } catch (error) {
      console.warn('[auth-storage] No se pudo parsear el usuario persistido', error);
      return null;
    }
  }
  if (!value.id || !value.email) return null;
  const role = value.role ?? value.rol ?? 'user';
  // Detectar id/nombre del tipo de usuario en distintas formas que pueda venir del backend
  const tipoUsuarioId = value.tipoUsuarioId ?? value.tipo_usuario_id ?? (value.tipo_usuario && value.tipo_usuario.id) ?? undefined;
  const tipoUsuarioNombre = value.tipoUsuarioNombre ?? value.tipo_usuario?.nombre ?? value.tipo_usuario_nombre ?? undefined;
  return {
    id: String(value.id),
    nombre: value.nombre ?? 'Usuario',
    email: value.email,
    role: role === 'admin' ? 'admin' : 'user',
    tipoUsuarioNombre,
    tipoUsuarioId,
  };
}

export const authStorage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, token);
  },
  clearToken() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
  },
  getUser(): StoredUser | null {
    if (typeof window === 'undefined') return null;
    return normalizeUser(localStorage.getItem(USER_KEY));
  },
  setUser(user: StoredUser) {
    if (typeof window === 'undefined') return;
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clearUser() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(USER_KEY);
  },
  clearAll() {
    this.clearToken();
    this.clearUser();
  },
};
