import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { UserResponse } from "@/api/types";
import { getMe, getStoredToken, login as apiLogin, signUp as apiSignUp } from "@/api/client";

const TOKEN_KEY = "medora_token";

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  setUser: (user: UserResponse | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!token;

  const loadUser = useCallback(async () => {
    const t = getStoredToken();
    if (!t) {
      setToken(null);
      setUser(null);
      setIsLoading(false);
      return;
    }
    setToken(t);
    try {
      const u = await Promise.race([
        getMe(),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error("Auth timeout")), 8000)
        ),
      ]);
      setUser(u);
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await apiLogin({ email, password });
      localStorage.setItem(TOKEN_KEY, res.access_token);
      setToken(res.access_token);
      const u = await getMe();
      setUser(u);
    },
    []
  );

  const signUp = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const res = await apiSignUp({ email, password, full_name: fullName });
      localStorage.setItem(TOKEN_KEY, res.access_token);
      setToken(res.access_token);
      const u = await getMe();
      setUser(u);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated,
      login,
      signUp,
      logout,
      setUser,
    }),
    [user, token, isLoading, isAuthenticated, login, signUp, logout]
  );

  if (isLoading) {
    return (
      <AuthContext.Provider value={value}>
        <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
          <p className="text-[var(--muted-foreground)] text-sm">Loading…</p>
        </div>
      </AuthContext.Provider>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
