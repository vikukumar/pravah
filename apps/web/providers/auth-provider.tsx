"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { UserProfile } from "@pravah/shared-types";

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string, refreshToken: string, userData: any) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const checkInitialSetupAndUser = async () => {
    try {
      // Check setup status first
      const setupStatus = await fetchApi<{ is_initialized: boolean }>("/setup/status");
      if (!setupStatus.is_initialized && pathname !== "/setup") {
        router.push("/setup");
        setIsLoading(false);
        return;
      }
    } catch {
      // If API not reachable yet
    }

    const token = localStorage.getItem("pravah_access_token");
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const data = await fetchApi<UserProfile>("/auth/me");
      setUser(data);
    } catch {
      // Invalid or expired token
      localStorage.removeItem("pravah_access_token");
      localStorage.removeItem("pravah_refresh_token");
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkInitialSetupAndUser();
  }, [pathname]);

  const login = (token: string, refreshToken: string, userData: any) => {
    localStorage.setItem("pravah_access_token", token);
    localStorage.setItem("pravah_refresh_token", refreshToken);
    setUser(userData);
  };

  const logout = async () => {
    try {
      await fetchApi("/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors on logout
    }
    localStorage.removeItem("pravah_access_token");
    localStorage.removeItem("pravah_refresh_token");
    localStorage.removeItem("pravah_active_org_id");
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser: checkInitialSetupAndUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
