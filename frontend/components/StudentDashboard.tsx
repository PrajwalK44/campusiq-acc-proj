"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiRequest } from "@/lib/api";
import { QueryRecord, Ticket } from "@/types";

export default function StudentDashboard() {
  const { token } = useAuth();
  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState("Academics");
  const [currentResult, setCurrentResult] = useState<QueryRecord | null>(null);
  const [history, setHistory] = useState<QueryRecord[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, string>>({});
  const [escalating, setEscalating] = useState(false);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await apiRequest<QueryRecord[]>("/queries", {}, token);
      setHistory(data);
    } catch (e) {
      console.error("Failed to load history", e);
    }
  }, [token]);

  const fetchTickets = useCallback(async () => {
    try {
      const data = await apiRequest<Ticket[]>("/tickets", {}, token);
      setTickets(data);
    } catch (e) {
      console.error("Failed to load tickets", e);
    }
  }, [token]);

  useEffect(() => {
    fetchHistory();
    fetchTickets();
  }, [fetchHistory, fetchTickets]);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setCurrentResult(null);

    try {
      const res = await apiRequest<QueryRecord>(
        "/queries",
        {
          method: "POST",
          body: JSON.stringify({ question, category }),
        },
        token
      );
      setCurrentResult(res);
      setQuestion("");
      fetchHistory();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Error asking query: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (queryId: string, rating: "HELPFUL" | "NOT_HELPFUL") => {
    try {
      await apiRequest(
        `/queries/${queryId}/feedback`,
        {
          method: "POST",
          body: JSON.stringify({ rating }),
        },
        token
      );
      setFeedbackGiven((prev) => ({ ...prev, [queryId]: rating }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Error submitting feedback: ${msg}`);
    }
  };

  const handleEscalateToTicket = async () => {
    if (!currentResult) return;
    setEscalating(true);
    try {
      await apiRequest(
        "/tickets",
        {
          method: "POST",
          body: JSON.stringify({
            original_question: currentResult.question,
            description: `Auto-escalated from AI assistant abstention/insufficient answer: "${currentResult.answer}"`,
            category: currentResult.category,
          }),
        },
        token
      );
      alert("Ticket submitted successfully to college faculty queue!");
      fetchTickets();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Failed to escalate ticket: ${msg}`);
    } finally {
      setEscalating(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Ask Question Card */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 mb-2">Ask Institutional Assistant</h2>
        <p className="text-sm text-gray-500 mb-4">
          Ask questions regarding academic guidelines, exams, attendance rules, or campus facilities.
          Answers are strictly grounded in official documents with citations.
        </p>

        <form onSubmit={handleAsk} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-3">
              <input
                type="text"
                placeholder="e.g. What is the minimum attendance requirement for semester exams?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="Academics">Academics</option>
                <option value="Examinations">Examinations</option>
                <option value="Hostel & Campus">Hostel & Campus</option>
                <option value="Placements">Placements</option>
                <option value="General">General</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="py-3 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition disabled:opacity-50"
            >
              {loading ? "Retrieving & Generating Answer..." : "Ask Assistant"}
            </button>
          </div>
        </form>
      </div>

      {/* Real-time Query Result Display */}
      {currentResult && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-blue-100 bg-blue-50/20">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold px-2.5 py-1 bg-blue-100 text-blue-800 rounded-full">
              Category: {currentResult.category}
            </span>
            <span
              className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                currentResult.answer_status === "ANSWERED"
                  ? "bg-green-100 text-green-800"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              Status: {currentResult.answer_status}
            </span>
          </div>

          <h3 className="font-semibold text-gray-900 text-lg mb-2">Q: {currentResult.question}</h3>
          <div className="p-4 bg-white rounded-xl border border-gray-200 text-gray-800 text-sm whitespace-pre-line leading-relaxed mb-4">
            {currentResult.answer}
          </div>

          {/* Grounded Citations & Sources */}
          {currentResult.sources && currentResult.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-600 mb-2">
                Official Document Citations:
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {currentResult.sources.map((src, i) => (
                  <div key={i} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                    <div className="font-semibold text-slate-800">
                      {src.document_title} (Page {src.page_number || "N/A"})
                    </div>
                    <p className="text-slate-600 mt-1 italic line-clamp-3">
                      &quot;{src.excerpt}&quot;
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Feedback & Escalation Action Buttons */}
          <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 font-medium">Was this helpful?</span>
              <button
                onClick={() => handleFeedback(currentResult.id, "HELPFUL")}
                disabled={!!feedbackGiven[currentResult.id]}
                className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                  feedbackGiven[currentResult.id] === "HELPFUL"
                    ? "bg-green-600 text-white border-green-600"
                    : "bg-white text-gray-700 hover:bg-gray-100 border-gray-200"
                }`}
              >
                Helpful
              </button>
              <button
                onClick={() => handleFeedback(currentResult.id, "NOT_HELPFUL")}
                disabled={!!feedbackGiven[currentResult.id]}
                className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                  feedbackGiven[currentResult.id] === "NOT_HELPFUL"
                    ? "bg-red-600 text-white border-red-600"
                    : "bg-white text-gray-700 hover:bg-gray-100 border-gray-200"
                }`}
              >
                Not Helpful
              </button>
            </div>

            {currentResult.answer_status === "ABSTAINED" && (
              <button
                onClick={handleEscalateToTicket}
                disabled={escalating}
                className="text-xs px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-lg shadow-sm transition"
              >
                {escalating ? "Escalating..." : "Escalate Query to Faculty"}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Two Column Layout: Recent Questions & Escalated Tickets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Queries */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="text-base font-bold text-gray-900 mb-4">My Recent Queries</h3>
          <div className="space-y-3">
            {history.length === 0 ? (
              <p className="text-sm text-gray-400">No query history yet.</p>
            ) : (
              history.slice(0, 5).map((q) => (
                <div key={q.id} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="flex justify-between items-start gap-2 mb-1">
                    <p className="font-semibold text-xs text-gray-900">{q.question}</p>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        q.answer_status === "ANSWERED"
                          ? "bg-green-100 text-green-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {q.answer_status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 line-clamp-2">{q.answer}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* My Escalated Tickets */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="text-base font-bold text-gray-900 mb-4">My Escalated Tickets</h3>
          <div className="space-y-3">
            {tickets.length === 0 ? (
              <p className="text-sm text-gray-400">No escalated tickets.</p>
            ) : (
              tickets.map((t) => (
                <div key={t.id} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="flex justify-between items-start gap-2 mb-1">
                    <span className="font-semibold text-xs text-gray-900">{t.original_question}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        t.status === "RESOLVED"
                          ? "bg-green-100 text-green-700"
                          : t.status === "IN_PROGRESS"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {t.status}
                    </span>
                  </div>
                  {t.faculty_response ? (
                    <div className="mt-2 p-2 bg-white rounded border border-green-200 text-xs text-gray-800">
                      <span className="font-bold text-green-700 block">Faculty Response:</span>
                      {t.faculty_response}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 italic mt-1">Pending faculty response...</p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
