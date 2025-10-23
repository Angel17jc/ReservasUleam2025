import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import { authApi, Credentials, UserProfile } from '@/api/rest/authApi';
import { authStorage } from '@/lib/auth-storage';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: UserProfile | null) => void;
  switchRole: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(authStorage.getUser());
  const [token, setToken] = useState<string | null>(authStorage.getToken());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = authStorage.getToken();
    if (!savedToken) {
      setIsLoading(false);
      return;
    }

    authApi
      .me()
      .then((me) => {
        setUser(me);
        authStorage.setUser(me);
        setToken(savedToken);
      })
      .catch(() => {
        authStorage.clearAll();
        setUser(null);
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (credentials: Credentials) => {
    const { token: newToken, user: authenticatedUser } = await authApi.login(credentials);
    authStorage.setToken(newToken);
    authStorage.setUser(authenticatedUser);
    setToken(newToken);
    setUser(authenticatedUser);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.warn('[auth] logout remoto falló', error);
    }
    authStorage.clearAll();
    setToken(null);
    setUser(null);
  };

  const switchRole = () => {
    setUser((prev) => {
      if (!prev) return prev;
      const nextRole = prev.rol === 'admin' ? 'usuario' : 'admin';
      const updated = { ...prev, rol: nextRole };
      authStorage.setUser(updated);
      return updated;
    });
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isAdmin: user?.rol === 'admin',
      isLoading,
      login,
      logout,
      setUser,
      switchRole,
    }),
    [user, token, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
