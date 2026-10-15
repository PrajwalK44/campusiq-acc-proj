"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function LoginForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("student@campusiq.edu");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to log in");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword("Password123!");
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-slate-900">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-xl font-bold text-xl mb-2">
            IQ
          </div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">CampusIQ</h1>
          <p className="text-sm text-gray-500">AI-Based Student Query Management System</p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-700 tracking-wider mb-1">
              Institutional Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-black bg-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              style={{ color: "#111827", backgroundColor: "#ffffff" }}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-gray-700 tracking-wider mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-black bg-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              style={{ color: "#111827", backgroundColor: "#ffffff" }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <div className="pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold uppercase text-gray-400 tracking-wider mb-2 text-center">
            Demo Credentials (Click to Autofill)
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => handleQuickSelect("student@campusiq.edu")}
              className="text-xs py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded font-medium text-center transition"
            >
              Student
            </button>
            <button
              onClick={() => handleQuickSelect("faculty@campusiq.edu")}
              className="text-xs py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded font-medium text-center transition"
            >
              Faculty
            </button>
            <button
              onClick={() => handleQuickSelect("admin@campusiq.edu")}
              className="text-xs py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded font-medium text-center transition"
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
