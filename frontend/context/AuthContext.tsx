"use client";

import React, { createContext, useContext, useState, useSyncExternalStore } from "react";
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

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getStoredToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("campusiq_token");
}

function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const userJson = sessionStorage.getItem("campusiq_user");
  if (!userJson) return null;
  try {
    return JSON.parse(userJson) as User;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const initialToken = useSyncExternalStore(subscribe, getStoredToken, () => null);
  const initialUser = useSyncExternalStore(subscribe, getStoredUser, () => null);

  const [token, setToken] = useState<string | null>(initialToken);
  const [user, setUser] = useState<User | null>(initialUser);

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
    <AuthContext.Provider value={{ user, token, login, logout, isLoading: false }}>
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
