"use client";

import { useEffect, useState } from "react";

import { LeavePolicyWarningBadge, LeavePolicyWarningBanner } from "@/components/LeavePolicyWarning";
import {
  approveLeaveRequest,
  fetchLeaveBalances,
  fetchLeaveRequests,
  fetchLeaveTypes,
  fetchStaff,
  getApiErrorMessage,
  rejectLeaveRequest,
} from "@/lib/api-client";
import type { LeaveBalance, LeaveRequest, LeaveStatus, LeaveType, User } from "@/types";

const CURRENT_YEAR = new Date().getFullYear();

const STATUS_COLORS: Record<LeaveStatus, string> = {
  PENDING: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  APPROVED: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  REJECTED: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  CANCELLED: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
};

function fmtDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString([], {
    month: "short", day: "numeric",
  });
}

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

type ReviewModal = { id: string; action: "approve" | "reject" };

export default function LeaveRequestsPage() {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [staff, setStaff] = useState<User[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [modal, setModal] = useState<ReviewModal | null>(null);
  const [reviewNote, setReviewNote] = useState("");
  const [acting, setActing] = useState(false);

  function reload() {
    setLoading(true);
    Promise.all([
      fetchLeaveRequests({ status: statusFilter || undefined }),
      fetchLeaveTypes(true),
      fetchStaff(),
      fetchLeaveBalances({ year: CURRENT_YEAR }),
    ])
      .then(([reqs, types, s, bal]) => { setRequests(reqs); setLeaveTypes(types); setStaff(s); setBalances(bal); })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load requests")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { reload(); }, [statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleReview() {
    if (!modal) return;
    setActing(true);
    setErrorMessage(null);
    try {
      if (modal.action === "approve") {
        await approveLeaveRequest(modal.id, reviewNote || undefined);
      } else {
        await rejectLeaveRequest(modal.id, reviewNote || undefined);
      }
      setModal(null);
      setReviewNote("");
      reload();
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Action failed"));
    } finally {
      setActing(false);
    }
  }

  const policyWarningCount = requests.filter((r) => r.exceeds_per_request_max).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Leave Requests</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Review and approve staff leave requests.</p>
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
      {policyWarningCount > 0 && (
        <LeavePolicyWarningBanner
          warning={`${policyWarningCount} request${policyWarningCount === 1 ? "" : "s"} exceed the configured per-request maximum and need careful review.`}
        />
      )}

      {/* Review modal */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/60">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900">
            <h2 className="text-base font-semibold text-slate-900 capitalize dark:text-slate-100">
              {modal.action} leave request
            </h2>
            {requests.find((r) => r.id === modal.id)?.policy_warning && (
              <div className="mt-3">
                <LeavePolicyWarningBanner
                  warning={requests.find((r) => r.id === modal.id)!.policy_warning!}
                />
              </div>
            )}
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
      ) : requests.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No requests found.</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Staff</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Type</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Period</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Days</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Remaining</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Reason</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Submitted</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {requests.map((req) => {
                const typeName = leaveTypes.find((t) => t.id === req.leave_type_id)?.name ?? "—";
                const staffName = staff.find((s) => s.id === req.user_id)?.name ?? "—";
                const balance = balances.find(
                  (b) => b.user_id === req.user_id && b.leave_type_id === req.leave_type_id && b.year === CURRENT_YEAR,
                );
                return (
                  <tr key={req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                    <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{staffName}</td>
                    <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">
                      {typeName}
                      <LeavePolicyWarningBadge warning={req.policy_warning} />
                    </td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                      {fmtDate(req.start_date)}
                      {req.start_date !== req.end_date && <> – {fmtDate(req.end_date)}</>}
                    </td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{req.total_days}</td>
                    <td className="px-4 py-3">
                      {balance ? (
                        <span className={`font-medium ${balance.remaining_days <= 3 ? "text-rose-600 dark:text-rose-400" : "text-slate-700 dark:text-slate-300"}`}>
                          {balance.remaining_days} / {balance.balance_days}
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500">—</span>
                      )}
                    </td>
                    <td className="max-w-xs px-4 py-3 text-slate-500 dark:text-slate-400">
                      <span className="line-clamp-2">{req.reason ?? "—"}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{fmtDateTime(req.created_at)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[req.status]}`}>
                        {req.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {req.status === "PENDING" ? (
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => setModal({ id: req.id, action: "approve" })}
                            className="rounded bg-teal-700 px-2.5 py-1 text-xs font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            onClick={() => setModal({ id: req.id, action: "reject" })}
                            className="rounded bg-rose-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-rose-700"
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs italic text-slate-400 dark:text-slate-500">{req.reviewer_note ?? ""}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
