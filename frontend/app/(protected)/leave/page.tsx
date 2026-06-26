"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { LeavePolicyWarningBadge, LeavePolicyWarningBanner } from "@/components/LeavePolicyWarning";
import {
  adjustLeaveBalance,
  cancelLeaveRequest,
  createLeaveRequest,
  fetchLeaveBalances,
  fetchLeaveRequests,
  fetchLeaveTypes,
  fetchStaff,
  getApiErrorMessage,
} from "@/lib/api-client";
import { calendarYearsFromHire, isDateInCalendarYear } from "@/lib/leave-years";
import type { LeaveBalance, LeaveRequest, LeaveStatus, LeaveType, User } from "@/types";

const CURRENT_YEAR = new Date().getFullYear();

const STATUS_COLORS: Record<LeaveStatus, string> = {
  PENDING: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  APPROVED: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  REJECTED: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  CANCELLED: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
};

const inputCls = "rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";
const labelCls = "flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300";

function fmtDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString([], {
    weekday: "short", month: "short", day: "numeric",
  });
}

function fmtShortDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso + "T00:00:00").toLocaleDateString([], { year: "numeric", month: "short", day: "numeric" });
}

// ── Balance card (staff view) ──────────────────────────────────────────────

function BalanceCard({ balance, leaveTypes, year }: {
  balance: LeaveBalance;
  leaveTypes: LeaveType[];
  year: number;
}) {
  const lt = leaveTypes.find((t) => t.id === balance.leave_type_id);
  const typeName = lt?.name ?? "—";
  const isAnnual = lt?.tenure_based ?? false;
  const pct = isAnnual && balance.balance_days > 0
    ? (balance.used_days / balance.balance_days) * 100
    : 0;
  const low = isAnnual && balance.remaining_days <= 3 && balance.balance_days > 0;

  if (!isAnnual) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <p className="truncate text-xs font-medium text-slate-500 dark:text-slate-400">{typeName}</p>
        <p className="mt-1 text-2xl font-bold text-slate-800 dark:text-slate-200">
          {balance.used_days}
          <span className="ml-1 text-sm font-normal text-slate-500 dark:text-slate-400">days used</span>
        </p>
        <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{year}</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <p className="truncate text-xs font-medium text-slate-500 dark:text-slate-400">{typeName}</p>
      <p className={`mt-1 text-2xl font-bold ${low ? "text-rose-600 dark:text-rose-400" : "text-teal-700 dark:text-teal-400"}`}>
        {balance.remaining_days}
        <span className="ml-1 text-sm font-normal text-slate-500 dark:text-slate-400">/ {balance.balance_days} days</span>
      </p>
      <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">Used {balance.used_days} · {year}</p>
      {balance.balance_days > 0 && (
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
          <div
            className={`h-full rounded-full ${pct >= 80 ? "bg-rose-500" : "bg-teal-500"}`}
            style={{ width: `${Math.min(100, pct)}%` }}
          />
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function LeavePage() {
  const { user, canManageStaff } = useAuth();
  const isAdmin = canManageStaff;

  const calendarYears = calendarYearsFromHire(user?.hire_date, CURRENT_YEAR + 1);

  // Shared data
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Staff view
  const [year, setYear] = useState(CURRENT_YEAR);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [myCurrentYearBalances, setMyCurrentYearBalances] = useState<LeaveBalance[]>([]);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ leave_type_id: "", start_date: "", end_date: "", reason: "" });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitSuccessMessage, setSubmitSuccessMessage] = useState<string | null>(null);
  const [acting, setActing] = useState(false);

  // Admin view
  const [staff, setStaff] = useState<User[]>([]);

  // Initial load
  useEffect(() => {
    const fetches: Promise<unknown>[] = [
      fetchLeaveTypes(),
      fetchLeaveRequests(),
      fetchLeaveBalances({ year }),
    ];
    if (isAdmin) fetches.push(fetchStaff());

    setLoading(true);
    Promise.all(fetches)
      .then(([types, reqs, bal, staffList]) => {
        setLeaveTypes(types as LeaveType[]);
        setRequests(reqs as LeaveRequest[]);
        setBalances(bal as LeaveBalance[]);
        // Track only the current user's current-year balances for the request form.
        setMyCurrentYearBalances(
          (bal as LeaveBalance[]).filter((b) => {
            const lt = (types as LeaveType[]).find((t) => t.id === b.leave_type_id);
            return b.user_id === user?.id && lt?.tenure_based;
          })
        );
        if (staffList) setStaff(staffList as User[]);
      })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load leave data")))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Re-fetch balances when year changes (staff view).
  // For past years with no rows yet, backfill from the current year's assigned types.
  useEffect(() => {
    if (loading) return; // skip during initial load
    setBalancesLoading(true);
    fetchLeaveBalances({ year })
      .then(async (bal) => {
        if (bal.length === 0 && year < CURRENT_YEAR && myAnnualBalances.length > 0) {
          await Promise.allSettled(
            myAnnualBalances.map((b) =>
              adjustLeaveBalance({
                user_id: user!.id,
                leave_type_id: b.leave_type_id,
                year,
                delta_days: 0,
                reason: "Backfill for past service year",
              })
            )
          );
          return fetchLeaveBalances({ year });
        }
        return bal;
      })
      .then(setBalances)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load balances")))
      .finally(() => setBalancesLoading(false));
  }, [year]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.leave_type_id || !form.start_date || !form.end_date) {
      setFormError("Please fill in all required fields.");
      return;
    }
    setActing(true);
    setFormError(null);
    setSubmitSuccessMessage(null);
    try {
      const created = await createLeaveRequest({
        leave_type_id: form.leave_type_id,
        start_date: form.start_date,
        end_date: form.end_date,
        reason: form.reason || null,
      });
      setShowForm(false);
      setForm({ leave_type_id: "", start_date: "", end_date: "", reason: "" });
      if (created.policy_warning) {
        setSubmitSuccessMessage(
          `Request submitted. ${created.policy_warning} Your manager will review it.`,
        );
      } else {
        setSubmitSuccessMessage("Leave request submitted.");
      }
      fetchLeaveRequests().then(setRequests);
      fetchLeaveBalances({ year }).then((bal) => {
        setBalances(bal);
        setMyCurrentYearBalances(bal.filter((b) => b.user_id === user?.id));
      });
    } catch (err) {
      setFormError(getApiErrorMessage(err, "Could not submit request"));
    } finally {
      setActing(false);
    }
  }

  async function handleCancel(id: string) {
    setActing(true);
    try {
      await cancelLeaveRequest(id);
      fetchLeaveRequests().then(setRequests);
      fetchLeaveBalances({ year }).then((bal) => {
        setBalances(bal);
        setMyCurrentYearBalances(bal.filter((b) => b.user_id === user?.id));
      });
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Could not cancel request"));
    } finally {
      setActing(false);
    }
  }

  // Admin: build per-employee summary from this year's balances
  const employeeSummaries = isAdmin
    ? staff.map((s) => {
        const empBalances = balances.filter((b) => b.user_id === s.id);
        const totalAllocated = empBalances.reduce((sum, b) => sum + Number(b.balance_days), 0);
        const totalUsed = empBalances.reduce((sum, b) => sum + Number(b.used_days), 0);
        const totalRemaining = empBalances.reduce((sum, b) => sum + Number(b.remaining_days), 0);
        return { user: s, totalAllocated, totalUsed, totalRemaining, count: empBalances.length };
      }).sort((a, b) => a.user.name.localeCompare(b.user.name))
    : null;

  const myRequests = isAdmin ? requests.filter((r) => r.user_id === user?.id) : requests;
  const pendingCount = myRequests.filter((r) => r.status === "PENDING").length;

  const activeLeaveTypes = leaveTypes.filter((t) => t.active);
  const selectedLeaveType = activeLeaveTypes.find((lt) => lt.id === form.leave_type_id);
  const formDuration =
    form.start_date && form.end_date && form.end_date >= form.start_date
      ? Math.max(1, Math.round((new Date(form.end_date).getTime() - new Date(form.start_date).getTime()) / 86400000) + 1)
      : 0;
  const formExceedsMax =
    selectedLeaveType != null
    && !selectedLeaveType.tenure_based
    && selectedLeaveType.default_days_per_year != null
    && formDuration > selectedLeaveType.default_days_per_year;
  const annualBalances = balances.filter((b) =>
    activeLeaveTypes.some((t) => t.id === b.leave_type_id && t.tenure_based)
  );
  const usageOnlyBalances = balances.filter((b) =>
    activeLeaveTypes.some((t) => t.id === b.leave_type_id && !t.tenure_based)
  );
  const myAnnualBalances = myCurrentYearBalances.filter((b) =>
    activeLeaveTypes.some((t) => t.id === b.leave_type_id && t.tenure_based)
  );

  const periodRequests = myRequests.filter((r) => isDateInCalendarYear(r.start_date, year));

  if (loading) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {isAdmin ? "Leave Overview" : "My Leave"}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {isAdmin ? "Click a staff card to view leave details." : "Submit and track your leave requests."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {pendingCount > 0 && (
            <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900 dark:text-amber-300">
              {pendingCount} pending
            </span>
          )}
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
          >
            {showForm ? "Cancel" : "New request"}
          </button>
        </div>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}
      {submitSuccessMessage && (
        <p className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800 dark:border-teal-800 dark:bg-teal-950 dark:text-teal-200">
          {submitSuccessMessage}
        </p>
      )}

      {/* ── Admin: staff summary cards ─────────────────────────────────── */}
      {isAdmin && employeeSummaries && (
        <div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {employeeSummaries.length === 0 ? (
              <p className="col-span-full text-sm text-slate-500 dark:text-slate-400">No staff found.</p>
            ) : employeeSummaries.map(({ user: s, totalAllocated, totalUsed, totalRemaining, count }) => (
              <Link
                key={s.id}
                href={`/leave/staff/${s.id}`}
                className="rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-teal-400 hover:shadow-md dark:border-slate-700 dark:bg-slate-900 dark:hover:border-teal-600"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-slate-100">{s.name}</p>
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                      Hired {fmtShortDate(s.hire_date ?? null)}
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                    {CURRENT_YEAR}
                  </span>
                </div>
                {count > 0 ? (
                  <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-lg font-bold text-slate-800 dark:text-slate-200">{totalAllocated}</p>
                      <p className="text-xs text-slate-400 dark:text-slate-500">Allocated</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-slate-800 dark:text-slate-200">{totalUsed}</p>
                      <p className="text-xs text-slate-400 dark:text-slate-500">Used</p>
                    </div>
                    <div>
                      <p className={`text-lg font-bold ${totalRemaining <= 3 ? "text-rose-600 dark:text-rose-400" : "text-teal-700 dark:text-teal-400"}`}>
                        {totalRemaining}
                      </p>
                      <p className="text-xs text-slate-400 dark:text-slate-500">Remaining</p>
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 text-xs text-slate-400 dark:text-slate-500">No balances for {CURRENT_YEAR}.</p>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Staff: year selector + balance cards ──────────────────────── */}
      {!isAdmin && (
        <>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Year</span>
            <div className="flex flex-wrap gap-1">
              {calendarYears.map((y) => (
                <button
                  key={y}
                  type="button"
                  onClick={() => setYear(y)}
                  className={`rounded-md px-3 py-1 text-sm font-medium transition ${
                    year === y
                      ? "bg-teal-700 text-white dark:bg-teal-600"
                      : "border border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800"
                  }`}
                >
                  {y}
                </button>
              ))}
            </div>
          </div>

          {balancesLoading ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
          ) : annualBalances.length === 0 && usageOnlyBalances.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">No annual leave or recorded usage for {year}.</p>
          ) : (
            <>
              {annualBalances.length > 0 && (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {annualBalances.map((b) => (
                    <BalanceCard key={b.id} balance={b} leaveTypes={leaveTypes} year={year} />
                  ))}
                </div>
              )}
              {usageOnlyBalances.length > 0 && (
                <div className={annualBalances.length > 0 ? "mt-4" : ""}>
                  {annualBalances.length > 0 && (
                    <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Other leave used
                    </h2>
                  )}
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                    {usageOnlyBalances.map((b) => (
                      <BalanceCard key={b.id} balance={b} leaveTypes={leaveTypes} year={year} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* ── New request form (all roles) ──────────────────────────────── */}
      {showForm && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-4 text-base font-semibold text-slate-900 dark:text-slate-100">New Leave Request</h2>
          {activeLeaveTypes.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No leave types are configured. Contact your manager.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className={labelCls}>
                  Leave type *
                  <select
                    value={form.leave_type_id}
                    onChange={(e) => setForm((f) => ({ ...f, leave_type_id: e.target.value }))}
                    required className={inputCls}
                  >
                    <option value="">Select…</option>
                    {activeLeaveTypes.map((lt) => {
                      const bal = balances.find(
                        (b) => b.leave_type_id === lt.id && b.year === year
                      );
                      let suffix = "";
                      if (lt.tenure_based) {
                        suffix = ` (${bal?.remaining_days ?? "—"} days remaining)`;
                      } else if (lt.default_days_per_year != null) {
                        suffix = ` (max ${lt.default_days_per_year} days/request)`;
                      }
                      return (
                        <option key={lt.id} value={lt.id}>
                          {lt.name}{suffix}
                        </option>
                      );
                    })}
                  </select>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className={labelCls}>
                    Start date *
                    <input type="date" value={form.start_date}
                      onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
                      required className={inputCls} />
                  </label>
                  <label className={labelCls}>
                    End date *
                    <input type="date" value={form.end_date} min={form.start_date}
                      onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
                      required className={inputCls} />
                  </label>
                </div>
              </div>
              <label className={labelCls}>
                Reason (optional)
                <input type="text" value={form.reason}
                  onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
                  maxLength={500} placeholder="Brief explanation" className={inputCls} />
              </label>
              {form.start_date && form.end_date && form.end_date >= form.start_date && (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Duration:{" "}
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    {formDuration} day(s)
                  </span>
                </p>
              )}
              {formExceedsMax && selectedLeaveType?.default_days_per_year != null && (
                <LeavePolicyWarningBanner
                  warning={`This request is ${formDuration} days, which exceeds the usual maximum of ${selectedLeaveType.default_days_per_year} days per request. You can still submit it for manager review.`}
                />
              )}
              {formError && <p className="text-sm text-rose-600 dark:text-rose-400">{formError}</p>}
              <div className="flex gap-3">
                <button type="submit" disabled={acting}
                  className="rounded-lg bg-teal-700 px-5 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700">
                  {acting ? "…" : "Submit request"}
                </button>
                <button type="button" onClick={() => { setShowForm(false); setFormError(null); }}
                  className="rounded-lg border border-slate-300 px-5 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800">
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* ── My requests ───────────────────────────────────────────────── */}
      <div>
        {isAdmin && <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">My Requests</h2>}
        {periodRequests.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No leave requests for this period.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Period</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Days</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Reason</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Note</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {periodRequests.map((req) => {
                  const typeName = leaveTypes.find((t) => t.id === req.leave_type_id)?.name ?? "—";
                  return (
                    <tr key={req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                      <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">
                        {typeName}
                        <LeavePolicyWarningBadge warning={req.policy_warning} />
                      </td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                        {fmtDate(req.start_date)}{req.start_date !== req.end_date && <> – {fmtDate(req.end_date)}</>}
                      </td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{req.total_days}</td>
                      <td className="max-w-xs px-4 py-3 text-slate-500 dark:text-slate-400">
                        <span className="line-clamp-1">{req.reason ?? "—"}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[req.status]}`}>
                          {req.status}
                        </span>
                      </td>
                      <td className="max-w-xs px-4 py-3 text-xs italic text-slate-400 dark:text-slate-500">
                        {req.reviewer_note ?? ""}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {req.status === "PENDING" && (
                          <button type="button" disabled={acting} onClick={() => handleCancel(req.id)}
                            className="text-xs text-rose-600 hover:underline dark:text-rose-400">
                            Cancel
                          </button>
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
    </div>
  );
}
