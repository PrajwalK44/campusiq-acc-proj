"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiRequest } from "@/lib/api";
import { AnalyticsOverview, DocumentRecord } from "@/types";

export default function AdminDashboard() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState("Academics");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const fetchOverview = useCallback(async () => {
    try {
      const data = await apiRequest<AnalyticsOverview>("/analytics/overview", {}, token);
      setOverview(data);
    } catch (e) {
      console.error("Failed to fetch analytics overview", e);
    }
  }, [token]);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await apiRequest<DocumentRecord[]>("/documents", {}, token);
      setDocuments(data);
    } catch (e) {
      console.error("Failed to fetch documents", e);
    }
  }, [token]);

  useEffect(() => {
    fetchOverview();
    fetchDocuments();
  }, [fetchOverview, fetchDocuments]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle.trim()) {
      alert("Please provide a title and choose a PDF file.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("title", uploadTitle);
    formData.append("category", uploadCategory);
    formData.append("file", uploadFile);

    try {
      await apiRequest<DocumentRecord>(
        "/documents",
        {
          method: "POST",
          body: formData,
        },
        token
      );
      alert("Document uploaded, extracted, and indexed into ChromaDB successfully!");
      setUploadTitle("");
      setUploadFile(null);
      fetchDocuments();
      fetchOverview();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Upload/Indexing failed: ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document and purge its vectors from ChromaDB?")) {
      return;
    }
    try {
      await apiRequest(`/documents/${id}`, { method: "DELETE" }, token);
      fetchDocuments();
      fetchOverview();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Delete failed: ${msg}`);
    }
  };

  const handleReindexDoc = async (id: string) => {
    try {
      await apiRequest(`/documents/${id}/reindex`, { method: "POST" }, token);
      alert("Document reindexed successfully!");
      fetchDocuments();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      alert(`Reindexing failed: ${msg}`);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Administrator Console</h2>
        <p className="text-sm text-gray-500">
          Knowledge Base ingestion, ChromaDB vector sync, user oversight, and institutional analytics.
        </p>
      </div>

      {/* Analytics Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase">Total AI Queries</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{overview?.total_queries ?? 0}</p>
          <p className="text-xs text-green-600 mt-1">Answered: {overview?.answered_queries ?? 0}</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase">Abstained Queries</p>
          <p className="text-2xl font-bold text-amber-600 mt-2">{overview?.abstained_queries ?? 0}</p>
          <p className="text-xs text-gray-400 mt-1">Grounded abstentions</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase">Escalated Tickets</p>
          <p className="text-2xl font-bold text-blue-600 mt-2">{overview?.total_tickets ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">Open: {overview?.open_tickets ?? 0} | Resolved: {overview?.resolved_tickets ?? 0}</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase">Indexed Documents</p>
          <p className="text-2xl font-bold text-purple-600 mt-2">{overview?.indexed_documents ?? 0}</p>
          <p className="text-xs text-gray-400 mt-1">In ChromaDB Vector Store</p>
        </div>
      </div>

      {/* Document Upload Form */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <h3 className="text-base font-bold text-gray-900 mb-2">Ingest New College Document (PDF)</h3>
        <p className="text-xs text-gray-500 mb-4">
          Upload an official document. PyMuPDF will extract text with page numbers, split it into chunks, generate embeddings via Sentence-Transformers, and upsert vectors into ChromaDB.
        </p>

        <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Document Title</label>
            <input
              type="text"
              placeholder="e.g. Student Handbook 2026"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Category</label>
            <select
              value={uploadCategory}
              onChange={(e) => setUploadCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="Academics">Academics</option>
              <option value="Examinations">Examinations</option>
              <option value="Hostel & Campus">Hostel & Campus</option>
              <option value="Placements">Placements</option>
              <option value="General">General</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Select PDF File</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
              required
              className="w-full text-xs text-gray-500 file:mr-2 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={uploading}
              className="w-full py-2.5 px-4 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg text-sm transition disabled:opacity-50"
            >
              {uploading ? "Ingesting & Indexing..." : "Upload & Index PDF"}
            </button>
          </div>
        </form>
      </div>

      {/* Managed Documents List */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <h3 className="text-base font-bold text-gray-900 mb-4">Indexed Documents in Vector Store</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="p-3">Title</th>
                <th className="p-3">Filename</th>
                <th className="p-3">Category</th>
                <th className="p-3">Status</th>
                <th className="p-3">Chunks</th>
                <th className="p-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-gray-400">
                    No documents indexed yet. Upload an official PDF above.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="p-3 font-semibold text-gray-900">{doc.title}</td>
                    <td className="p-3 text-gray-500">{doc.original_filename}</td>
                    <td className="p-3">{doc.category}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          doc.processing_status === "INDEXED"
                            ? "bg-green-100 text-green-700"
                            : doc.processing_status === "PROCESSING"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {doc.processing_status}
                      </span>
                    </td>
                    <td className="p-3 font-mono">{doc.chunk_count}</td>
                    <td className="p-3 space-x-2">
                      <button
                        onClick={() => handleReindexDoc(doc.id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Re-index
                      </button>
                      <button
                        onClick={() => handleDeleteDoc(doc.id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
