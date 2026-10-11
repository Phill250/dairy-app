"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  UserRead, LoginResult, getMe, getAccessToken,
  login as apiLogin, logout as apiLogout, verifyTwoFactor as apiVerifyTwoFactor,
} from "@/lib/api";

interface AuthContextValue {
  user: UserRead | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  completeTwoFactor: (mfaToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshUser() {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await getMe());
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshUser();
  }, []);

  async function login(email: string, password: string): Promise<LoginResult> {
    const result = await apiLogin(email, password);
    if (result.status === "ok") await refreshUser();
    return result;
  }

  async function completeTwoFactor(mfaToken: string, code: string) {
    await apiVerifyTwoFactor(mfaToken, code);
    await refreshUser();
  }

  async function logout() {
    await apiLogout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, completeTwoFactor, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}