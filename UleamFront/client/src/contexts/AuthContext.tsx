import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import { authApi, Credentials, UserProfile, RegisterInput } from '@/api/rest/authApi';
import { authStorage } from '@/lib/auth-storage';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  roleLabel: string | null;
  login: (credentials: Credentials) => Promise<UserProfile>;
  register: (input: RegisterInput) => Promise<UserProfile>;
  logout: () => Promise<void>;
  setUser: (user: UserProfile | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // No rehidratar `user` desde localStorage inmediatamente to avoid showing stale role labels.
  // Mantener sólo el token y solicitar `/auth/me` para obtener el usuario real y actualizado.
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(authStorage.getToken());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = authStorage.getToken();
    if (!savedToken) {
      setIsLoading(false);
      return;
    }

    // Si tenemos token, validarlo y obtener el usuario actual desde el backend.
    authApi
      .me()
      .then((me) => {
        setUser(me);
        authStorage.setUser(me);
        setToken(savedToken);
      })
      .catch((err) => {
        console.warn('[auth] Falló rehidratación de usuario:', err);
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
    return authenticatedUser;
  };

  const register = async (input: RegisterInput) => {
    const { token: newToken, user: registeredUser } = await authApi.register(input);
    authStorage.setToken(newToken);
    authStorage.setUser(registeredUser);
    setToken(newToken);
    setUser(registeredUser);
    return registeredUser;
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

  const value = useMemo(() => {
    const isAdminComputed =
      Boolean(user?.tipoUsuarioId && Number(user.tipoUsuarioId) === 1) ||
      user?.role === 'admin' ||
      Boolean(user?.tipoUsuarioNombre && String(user.tipoUsuarioNombre).toLowerCase().includes('admin'));

    const roleLabelComputed = isAdminComputed
      ? 'Administrador'
      : user?.tipoUsuarioNombre ?? (user?.role === 'admin' ? 'Administrador' : 'Usuario');

    return {
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isAdmin: isAdminComputed,
      roleLabel: roleLabelComputed,
      isLoading,
      login,
      register,
      logout,
      setUser,
    };
  }, [user, token, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
