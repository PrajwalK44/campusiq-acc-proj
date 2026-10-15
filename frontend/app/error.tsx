"use client";

import React, { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-gray-200 p-6 text-center space-y-4">
        <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto text-xl font-bold">
          !
        </div>
        <h2 className="text-lg font-bold text-gray-900">Something went wrong</h2>
        <p className="text-xs text-gray-500">
          {error.message || "An unexpected error occurred while rendering the dashboard."}
        </p>
        <div className="flex gap-2 justify-center pt-2">
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition"
          >
            Try Again
          </button>
          <button
            onClick={() => {
              sessionStorage.clear();
              window.location.href = "/";
            }}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg transition"
          >
            Return to Login
          </button>
        </div>
      </div>
    </div>
  );
}
