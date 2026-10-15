"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, AuthResponse } from "@/types";
import { apiRequest } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    try {
      const storedToken = sessionStorage.getItem("campusiq_token");
      const storedUser = sessionStorage.getItem("campusiq_user");
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser) as User);
      }
    } catch (e) {
      console.error("Failed to restore session from storage", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    setToken(res.access_token);
    setUser(res.user);
    sessionStorage.setItem("campusiq_token", res.access_token);
    sessionStorage.setItem("campusiq_user", JSON.stringify(res.user));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    sessionStorage.removeItem("campusiq_token");
    sessionStorage.removeItem("campusiq_user");
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
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
