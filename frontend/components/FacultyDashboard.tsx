"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiRequest } from "@/lib/api";
import { Ticket } from "@/types";

export default function FacultyDashboard() {
  const { token } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [responseMessage, setResponseMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchTickets = useCallback(async () => {
    try {
      const data = await apiRequest<Ticket[]>("/tickets", {}, token);
      setTickets(data);
    } catch (e) {
      console.error("Failed to load tickets", e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const handleSelectTicket = (t: Ticket) => {
    setSelectedTicket(t);
    setResponseMessage(t.faculty_response || "");
  };

  const handleSubmitResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !responseMessage.trim()) return;

    setSubmitting(true);
    try {
      await apiRequest(
        `/tickets/${selectedTicket.id}/responses`,
        {
          method: "POST",
          body: JSON.stringify({
            faculty_response: responseMessage,
            status: "RESOLVED",
          }),
        },
        token
      );
      alert("Official response recorded successfully.");
      setSelectedTicket(null);
      setResponseMessage("");
      fetchTickets();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Error submitting response: ${msg}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Faculty Resolution Queue</h2>
        <p className="text-sm text-gray-500">
          Review, assign, and answer escalated student queries that were not resolved by the AI knowledge base.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Ticket List */}
        <div className="lg:col-span-1 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 space-y-3">
          <h3 className="font-bold text-sm text-gray-700 px-2">Assigned & Open Tickets ({tickets.length})</h3>
          {loading ? (
            <p className="text-xs text-gray-400 p-2">Loading ticket queue...</p>
          ) : tickets.length === 0 ? (
            <p className="text-xs text-gray-400 p-2">No tickets awaiting response.</p>
          ) : (
            tickets.map((t) => (
              <div
                key={t.id}
                onClick={() => handleSelectTicket(t)}
                className={`p-3 rounded-xl border cursor-pointer transition ${
                  selectedTicket?.id === t.id
                    ? "bg-blue-50 border-blue-300"
                    : "bg-gray-50 border-gray-200 hover:bg-gray-100"
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-bold text-blue-700 uppercase">{t.category}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                      t.status === "RESOLVED"
                        ? "bg-green-100 text-green-700"
                        : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {t.status}
                  </span>
                </div>
                <p className="text-xs font-semibold text-gray-900 line-clamp-1">{t.original_question}</p>
                <p className="text-[11px] text-gray-500 mt-1">Student: {t.student_name || "Anonymous"}</p>
              </div>
            ))
          )}
        </div>

        {/* Ticket Details & Resolution Form */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          {selectedTicket ? (
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold px-2.5 py-1 bg-blue-100 text-blue-800 rounded-full">
                    Category: {selectedTicket.category}
                  </span>
                  <span className="text-xs text-gray-400">
                    Created: {new Date(selectedTicket.created_at).toLocaleString()}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-gray-900">
                  Question: {selectedTicket.original_question}
                </h3>
                {selectedTicket.description && (
                  <p className="text-sm text-gray-600 mt-2 bg-gray-50 p-3 rounded-xl border border-gray-100">
                    Context / Details: {selectedTicket.description}
                  </p>
                )}
              </div>

              <form onSubmit={handleSubmitResponse} className="space-y-4 pt-4 border-t border-gray-100">
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-700">
                  Official Faculty Response
                </label>
                <textarea
                  rows={6}
                  value={responseMessage}
                  onChange={(e) => setResponseMessage(e.target.value)}
                  placeholder="Provide authoritative guidance, policy clarifications, or office hour instructions..."
                  required
                  className="w-full p-4 border border-gray-300 rounded-xl text-gray-900 bg-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm leading-relaxed"
                />

                <div className="flex justify-end gap-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="py-2.5 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition disabled:opacity-50 text-sm"
                  >
                    {submitting ? "Submitting..." : "Submit Response & Resolve"}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <p className="text-sm">Select a ticket from the left queue to review and submit a response.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
