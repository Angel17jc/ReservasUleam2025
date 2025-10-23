const TOKEN_KEY = 'uleam_token';
const USER_KEY = 'uleam_user';

type StoredUser = {
  id: string;
  nombre: string;
  email: string;
  rol: string;
};

function safeParseUser(value: string | null): StoredUser | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as StoredUser;
  } catch (error) {
    console.warn('[auth-storage] No se pudo parsear el usuario persistido', error);
    return null;
  }
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
    return safeParseUser(localStorage.getItem(USER_KEY));
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
