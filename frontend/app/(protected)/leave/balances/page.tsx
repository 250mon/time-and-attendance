"use client";

import React, { useEffect, useState } from "react";

import {
  adjustLeaveBalance,
  fetchLeaveAdjustments,
  fetchLeaveBalances,
  fetchLeaveTypes,
  fetchStaff,
  getApiErrorMessage,
} from "@/lib/api-client";
import type { LeaveBalance, LeaveBalanceAdjustment, LeaveType, User } from "@/types";

const CURRENT_YEAR = new Date().getFullYear();

type AdjustModal = {
  balance: LeaveBalance;
  typeName: string;
  staffName: string;
};

const inputCls = "rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

export default function LeaveBalancesPage() {
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [staff, setStaff] = useState<User[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [year, setYear] = useState(CURRENT_YEAR);
  const [userFilter, setUserFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [modal, setModal] = useState<AdjustModal | null>(null);
  const [form, setForm] = useState({ delta_days: "", reason: "" });
  const [formError, setFormError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);

  // Expanded row → adjustment history
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [adjustments, setAdjustments] = useState<LeaveBalanceAdjustment[]>([]);
  const [adjLoading, setAdjLoading] = useState(false);

  function reload() {
    setLoading(true);
    const params: { year: number; user_id?: string } = { year };
    if (userFilter) params.user_id = userFilter;

    Promise.all([fetchLeaveBalances(params), fetchStaff(), fetchLeaveTypes(true)])
      .then(([bal, s, lt]) => {
        setBalances(bal);
        setStaff(s);
        setLeaveTypes(lt);
      })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load balances")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { reload(); }, [year, userFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  function openModal(balance: LeaveBalance) {
    const typeName = leaveTypes.find((t) => t.id === balance.leave_type_id)?.name ?? "—";
    const staffName = staff.find((s) => s.id === balance.user_id)?.name ?? "Unknown";
    setModal({ balance, typeName, staffName });
    setForm({ delta_days: "", reason: "" });
    setFormError(null);
  }

  function toggleHistory(balanceId: string) {
    if (expandedId === balanceId) {
      setExpandedId(null);
      setAdjustments([]);
      return;
    }
    setExpandedId(balanceId);
    setAdjLoading(true);
    fetchLeaveAdjustments(balanceId)
      .then(setAdjustments)
      .catch(() => setAdjustments([]))
      .finally(() => setAdjLoading(false));
  }

  async function handleAdjust() {
    if (!modal) return;
    const delta = parseFloat(form.delta_days);
    if (isNaN(delta) || delta === 0) {
      setFormError("Enter a non-zero number of days (positive to add, negative to subtract).");
      return;
    }
    if (!form.reason.trim()) {
      setFormError("A reason is required.");
      return;
    }
    setActing(true);
    setFormError(null);
    try {
      await adjustLeaveBalance({
        user_id: modal.balance.user_id,
        leave_type_id: modal.balance.leave_type_id,
        year: modal.balance.year,
        delta_days: delta,
        reason: form.reason.trim(),
      });
      // Refresh history panel for this balance if it was open
      if (expandedId === modal.balance.id) {
        fetchLeaveAdjustments(modal.balance.id).then(setAdjustments);
      }
      setModal(null);
      reload();
    } catch (err) {
      setFormError(getApiErrorMessage(err, "Adjustment failed"));
    } finally {
      setActing(false);
    }
  }

  const years = [CURRENT_YEAR - 1, CURRENT_YEAR];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Leave Balances</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            View and adjust staff leave allocations. Carryover is applied automatically at the start of each year.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            <option value="">All staff</option>
            {staff.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

      {/* Adjust modal */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/60">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Adjust Balance</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {modal.staffName} · {modal.typeName} · {modal.balance.year}
            </p>
            <p className="mt-3 text-sm text-slate-700 dark:text-slate-300">
              Current allocation:{" "}
              <span className="font-medium">{modal.balance.balance_days} days</span>
              {modal.balance.carryover_days > 0 && (
                <span className="ml-1 text-indigo-600 dark:text-indigo-400">
                  +{modal.balance.carryover_days} carried over
                </span>
              )}
              {" · "}Used:{" "}
              <span className="font-medium">{modal.balance.used_days} days</span>
            </p>

            <div className="mt-4 space-y-3">
              <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
                Adjustment (days)
                <input
                  type="number"
                  step="0.5"
                  value={form.delta_days}
                  onChange={(e) => setForm((f) => ({ ...f, delta_days: e.target.value }))}
                  placeholder="+5 or -3"
                  className={inputCls}
                />
                <span className="text-xs text-slate-400 dark:text-slate-500">Positive = add days, negative = remove days</span>
              </label>
              <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
                Reason
                <input
                  type="text"
                  maxLength={500}
                  value={form.reason}
                  onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
                  placeholder="e.g. Policy correction, bonus days"
                  className={inputCls}
                />
              </label>
            </div>

            {formError && <p className="mt-2 text-sm text-rose-600 dark:text-rose-400">{formError}</p>}

            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setModal(null)}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={acting}
                onClick={handleAdjust}
                className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
              >
                {acting ? "…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : balances.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No balances found for {year}.</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Staff</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Leave Type</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Allocated</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Carryover</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Used</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Remaining</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {balances.map((b) => {
                const staffName = staff.find((s) => s.id === b.user_id)?.name ?? "—";
                const lt = leaveTypes.find((t) => t.id === b.leave_type_id);
                const typeName = lt?.name ?? "—";
                const isAnnual = lt?.tenure_based ?? false;
                const effective = b.balance_days + b.carryover_days;
                const pct = effective > 0 ? (b.used_days / effective) * 100 : 0;
                const low = b.remaining_days <= 3;
                const isExpanded = expandedId === b.id;

                return (
                  <React.Fragment key={b.id}>
                    <tr className={`hover:bg-slate-50 dark:hover:bg-slate-800 ${isExpanded ? "bg-slate-50 dark:bg-slate-800" : ""}`}>
                      <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{staffName}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{typeName}</td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">
                        {isAnnual ? b.balance_days : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {b.carryover_days > 0 ? (
                          <span className="font-medium text-indigo-600 dark:text-indigo-400">+{b.carryover_days}</span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{b.used_days}</td>
                      <td className="px-4 py-3 text-right">
                        {isAnnual ? (
                          <>
                            <span className={`font-medium ${low ? "text-rose-600 dark:text-rose-400" : "text-teal-700 dark:text-teal-400"}`}>
                              {b.remaining_days}
                            </span>
                            {effective > 0 && (
                              <div className="mt-1 ml-auto h-1.5 w-16 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                                <div
                                  className={`h-full rounded-full ${pct >= 80 ? "bg-rose-500" : "bg-teal-500"}`}
                                  style={{ width: `${Math.min(100, pct)}%` }}
                                />
                              </div>
                            )}
                          </>
                        ) : (
                          <span className="text-slate-400 text-xs">tracking only</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-3">
                          <button
                            type="button"
                            onClick={() => toggleHistory(b.id)}
                            className="text-xs text-slate-500 hover:underline dark:text-slate-400"
                          >
                            {isExpanded ? "Hide history" : "History"}
                          </button>
                          {isAnnual && (
                            <button
                              type="button"
                              onClick={() => openModal(b)}
                              className="text-xs font-medium text-teal-700 hover:underline dark:text-teal-400"
                            >
                              Adjust
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-slate-50 dark:bg-slate-800/50">
                        <td colSpan={7} className="px-6 py-3">
                          {adjLoading ? (
                            <p className="text-xs text-slate-500 dark:text-slate-400">Loading…</p>
                          ) : adjustments.length === 0 ? (
                            <p className="text-xs text-slate-400 dark:text-slate-500">No manual adjustments recorded.</p>
                          ) : (
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="text-left text-slate-500 dark:text-slate-400">
                                  <th className="pb-1 pr-4 font-medium">Date</th>
                                  <th className="pb-1 pr-4 font-medium">Change</th>
                                  <th className="pb-1 font-medium">Reason</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                {adjustments.map((a) => (
                                  <tr key={a.id}>
                                    <td className="py-1 pr-4 text-slate-500 dark:text-slate-400">
                                      {new Date(a.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="py-1 pr-4">
                                      <span className={`font-semibold ${a.delta_days > 0 ? "text-teal-700 dark:text-teal-400" : "text-rose-600 dark:text-rose-400"}`}>
                                        {a.delta_days > 0 ? "+" : ""}{a.delta_days}d
                                      </span>
                                    </td>
                                    <td className="py-1 text-slate-700 dark:text-slate-300">{a.reason}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
