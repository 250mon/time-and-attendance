"use client";

import { useEffect, useState } from "react";

import { fetchAuditLogs, getApiErrorMessage } from "@/lib/api-client";
import type { AuditLog } from "@/types";

const ACTION_LABELS: Record<string, string> = {
  CORRECTION_APPROVED: "Correction Approved",
  CORRECTION_REJECTED: "Correction Rejected",
  LEAVE_APPROVED: "Leave Approved",
  LEAVE_REJECTED: "Leave Rejected",
  BALANCE_ADJUSTED: "Balance Adjusted",
  MONTH_LOCKED: "Month Locked",
  MONTH_UNLOCKED: "Month Unlocked",
  REPORT_EXPORTED: "Report Exported",
};

const ACTION_COLORS: Record<string, string> = {
  CORRECTION_APPROVED: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  CORRECTION_REJECTED: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  LEAVE_APPROVED: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  LEAVE_REJECTED: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  BALANCE_ADJUSTED: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  MONTH_LOCKED: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  MONTH_UNLOCKED: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  REPORT_EXPORTED: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
};

function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function fmtMetadata(extra_data: Record<string, unknown> | null, action: string): string {
  if (!extra_data) return "";
  if (action === "MONTH_LOCKED" || action === "MONTH_UNLOCKED") {
    return `${extra_data.year}-${String(extra_data.month).padStart(2, "0")}`;
  }
  if (action === "BALANCE_ADJUSTED") {
    const sign = (extra_data.delta_days as number) > 0 ? "+" : "";
    return `${sign}${extra_data.delta_days} days · ${extra_data.reason}`;
  }
  if (action === "LEAVE_APPROVED" || action === "LEAVE_REJECTED") {
    return `${extra_data.start_date} – ${extra_data.end_date} (${extra_data.total_days ?? "?"} days)`;
  }
  if (action === "CORRECTION_APPROVED" || action === "CORRECTION_REJECTED") {
    return `Work date: ${extra_data.work_date}`;
  }
  if (action === "REPORT_EXPORTED") {
    return `${extra_data.report_type}`;
  }
  return JSON.stringify(extra_data);
}

const PAGE_SIZE = 50;
const ALL_ACTIONS = Object.keys(ACTION_LABELS);

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  function reload(pageNum: number = 0) {
    setLoading(true);
    fetchAuditLogs({
      action: actionFilter || undefined,
      limit: PAGE_SIZE + 1,
      offset: pageNum * PAGE_SIZE,
    })
      .then((data) => {
        setHasMore(data.length > PAGE_SIZE);
        setLogs(data.slice(0, PAGE_SIZE));
      })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load audit log")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { setPage(0); reload(0); }, [actionFilter]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { reload(page); }, [page]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Audit Log</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Record of all management actions.</p>
        </div>
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          <option value="">All actions</option>
          {ALL_ACTIONS.map((a) => (
            <option key={a} value={a}>{ACTION_LABELS[a]}</option>
          ))}
        </select>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : logs.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No audit log entries found.</p>
      ) : (
        <>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">When</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Actor</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Action</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap dark:text-slate-400">
                      {fmtDateTime(log.created_at)}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{log.actor_name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          ACTION_COLORS[log.action] ?? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        {ACTION_LABELS[log.action] ?? log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                      {fmtMetadata(log.extra_data, log.action)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="rounded-md border border-slate-300 px-3 py-1.5 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-600 dark:hover:bg-slate-800"
            >
              Previous
            </button>
            <span>Page {page + 1}</span>
            <button
              type="button"
              disabled={!hasMore}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-md border border-slate-300 px-3 py-1.5 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-600 dark:hover:bg-slate-800"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
