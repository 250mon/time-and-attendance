"use client";

import { useEffect, useState } from "react";

import {
  approveCorrection,
  fetchCorrections,
  getApiErrorMessage,
  rejectCorrection,
} from "@/lib/api-client";
import type { AttendanceCorrectionRequest, CorrectionStatus } from "@/types";

const STATUS_COLORS: Record<CorrectionStatus, string> = {
  PENDING: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  APPROVED: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  REJECTED: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  CANCELLED: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
};

function fmtDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString([], {
    weekday: "short", month: "short", day: "numeric",
  });
}

function fmtTime(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

type ReviewModal = { id: string; action: "approve" | "reject" };

export default function CorrectionsPage() {
  const [corrections, setCorrections] = useState<AttendanceCorrectionRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("PENDING");
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [modal, setModal] = useState<ReviewModal | null>(null);
  const [reviewNote, setReviewNote] = useState("");
  const [acting, setActing] = useState(false);

  function reload() {
    setLoading(true);
    fetchCorrections({ status: statusFilter || undefined })
      .then(setCorrections)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load corrections")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { reload(); }, [statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleReview() {
    if (!modal) return;
    setActing(true);
    setErrorMessage(null);
    try {
      if (modal.action === "approve") {
        await approveCorrection(modal.id, reviewNote || undefined);
      } else {
        await rejectCorrection(modal.id, reviewNote || undefined);
      }
      setModal(null);
      setReviewNote("");
      reload();
    } catch (e) {
      setErrorMessage(getApiErrorMessage(e, "Action failed"));
    } finally {
      setActing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Correction Requests</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Review and approve staff attendance corrections.</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="">All</option>
        </select>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

      {/* Review modal */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/60">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900">
            <h2 className="text-base font-semibold text-slate-900 capitalize dark:text-slate-100">
              {modal.action} correction
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              You may leave a note for the staff member.
            </p>
            <textarea
              value={reviewNote}
              onChange={(e) => setReviewNote(e.target.value)}
              placeholder="Reviewer note (optional)"
              rows={3}
              className="mt-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
            />
            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => { setModal(null); setReviewNote(""); }}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={acting}
                onClick={handleReview}
                className={`rounded-md px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 ${
                  modal.action === "approve"
                    ? "bg-teal-700 hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
                    : "bg-rose-600 hover:bg-rose-700"
                }`}
              >
                {acting ? "…" : modal.action === "approve" ? "Approve" : "Reject"}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : corrections.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No corrections found.</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Date</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Corrected In</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Corrected Out</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Reason</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Submitted</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {corrections.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                  <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{fmtDate(c.work_date)}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{fmtTime(c.corrected_clock_in)}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{fmtTime(c.corrected_clock_out)}</td>
                  <td className="max-w-xs px-4 py-3 text-slate-600 dark:text-slate-400">
                    <span className="line-clamp-2">{c.reason}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{fmtDateTime(c.created_at)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[c.status]}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {c.status === "PENDING" && (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setModal({ id: c.id, action: "approve" })}
                          className="rounded bg-teal-700 px-2.5 py-1 text-xs font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => setModal({ id: c.id, action: "reject" })}
                          className="rounded bg-rose-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-rose-700"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                    {c.reviewer_note && (
                      <span className="text-xs italic text-slate-400 dark:text-slate-500">{c.reviewer_note}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
