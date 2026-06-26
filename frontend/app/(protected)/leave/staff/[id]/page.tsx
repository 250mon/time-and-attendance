"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { LeavePolicyWarningBadge } from "@/components/LeavePolicyWarning";
import {
  adjustLeaveBalance,
  fetchLeaveBalances,
  fetchLeaveRequests,
  fetchLeaveTypes,
  fetchStaffMember,
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

function fmtDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString([], {
    weekday: "short", month: "short", day: "numeric",
  });
}

function fmtShortDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso + "T00:00:00").toLocaleDateString([], {
    year: "numeric", month: "short", day: "numeric",
  });
}

export default function StaffLeaveDetailPage() {
  const { id } = useParams<{ id: string }>();

  const [staffMember, setStaffMember] = useState<User | null>(null);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [year, setYear] = useState(CURRENT_YEAR);
  const [loading, setLoading] = useState(true);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load staff member, leave types, and initial balances + requests.
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchStaffMember(id),
      fetchLeaveTypes(),
      fetchLeaveBalances({ year, user_id: id }),
      fetchLeaveRequests({ user_id: id }),
    ])
      .then(([member, types, bal, reqs]) => {
        setStaffMember(member);
        setLeaveTypes(types);
        setBalances(bal);
        setRequests(reqs);
      })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load leave data")))
      .finally(() => setLoading(false));
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reload balances when year changes, backfilling past years if needed.
  useEffect(() => {
    if (loading) return;
    setBalancesLoading(true);
    fetchLeaveBalances({ year, user_id: id })
      .then(async (bal) => {
        if (bal.length === 0 && year < CURRENT_YEAR) {
          const current = await fetchLeaveBalances({ year: CURRENT_YEAR, user_id: id });
          const annualCurrent = current.filter((b) =>
            leaveTypes.some((t) => t.id === b.leave_type_id && t.tenure_based)
          );
          if (annualCurrent.length > 0) {
            await Promise.allSettled(
              annualCurrent.map((b) =>
                adjustLeaveBalance({
                  user_id: id,
                  leave_type_id: b.leave_type_id,
                  year,
                  delta_days: 0,
                  reason: "Backfill for past service year",
                })
              )
            );
            return fetchLeaveBalances({ year, user_id: id });
          }
        }
        return bal;
      })
      .then(setBalances)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load balances")))
      .finally(() => setBalancesLoading(false));
  }, [year]); // eslint-disable-line react-hooks/exhaustive-deps

  const calendarYears = calendarYearsFromHire(staffMember?.hire_date, CURRENT_YEAR + 1);

  const periodRequests = requests.filter((r) => isDateInCalendarYear(r.start_date, year));

  if (loading) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>;
  }

  if (!staffMember) {
    return <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage ?? "Staff member not found."}</p>;
  }

  const annualBalances = balances.filter((b) =>
    leaveTypes.some((t) => t.id === b.leave_type_id && t.tenure_based)
  );
  const usageOnlyBalances = balances.filter((b) =>
    leaveTypes.some((t) => t.id === b.leave_type_id && !t.tenure_based)
  );

  const totalAllocated = annualBalances.reduce((s, b) => s + Number(b.balance_days), 0);
  const totalUsed = annualBalances.reduce((s, b) => s + Number(b.used_days), 0);
  const totalRemaining = annualBalances.reduce((s, b) => s + Number(b.remaining_days), 0);

  return (
    <div className="space-y-6">
      {/* Back link + header */}
      <div>
        <Link
          href="/leave"
          className="text-sm text-teal-700 hover:underline dark:text-teal-400"
        >
          ← Leave Overview
        </Link>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {staffMember.name}
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {staffMember.role} · {staffMember.employment_type?.replace("_", " ")} ·{" "}
              Hired {fmtShortDate(staffMember.hire_date ?? null)}
            </p>
          </div>

          {/* Summary totals for selected year */}
          {annualBalances.length > 0 && (
            <div className="flex gap-6 rounded-xl border border-slate-200 bg-white px-6 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              {[
                { label: "Allocated", value: totalAllocated },
                { label: "Used", value: totalUsed },
                { label: "Remaining", value: totalRemaining, highlight: true },
              ].map(({ label, value, highlight }) => (
                <div key={label} className="text-center">
                  <p className={`text-xl font-bold ${highlight ? "text-teal-700 dark:text-teal-400" : "text-slate-800 dark:text-slate-200"}`}>
                    {value}
                  </p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">{label}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {errorMessage && (
        <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
      )}

      {/* Calendar year selector */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Year</span>
        <div className="flex flex-wrap gap-1">
          {calendarYears.map((y) => (
            <button
              key={y}
              type="button"
              onClick={() => setYear(y)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition ${
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

      {/* Annual leave balances */}
      <div>
        <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">
          Annual leave · {year}
        </h2>
        {balancesLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
        ) : annualBalances.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No annual leave balance for {year}.
          </p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Leave type</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Allocated</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Used</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Remaining</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400 w-32">Usage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {annualBalances.map((b) => {
                  const typeName = leaveTypes.find((t) => t.id === b.leave_type_id)?.name ?? "—";
                  const pct = b.balance_days > 0 ? (b.used_days / b.balance_days) * 100 : 0;
                  const low = b.remaining_days <= 3 && b.balance_days > 0;
                  return (
                    <tr key={b.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                      <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{typeName}</td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{b.balance_days}</td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{b.used_days}</td>
                      <td className="px-4 py-3 text-right">
                        <span className={`font-semibold ${low ? "text-rose-600 dark:text-rose-400" : "text-teal-700 dark:text-teal-400"}`}>
                          {b.remaining_days}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {b.balance_days > 0 ? (
                          <div className="flex items-center gap-2">
                            <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                              <div
                                className={`h-full rounded-full ${pct >= 80 ? "bg-rose-500" : "bg-teal-500"}`}
                                style={{ width: `${Math.min(100, pct)}%` }}
                              />
                            </div>
                            <span className="w-8 text-right text-xs text-slate-400 dark:text-slate-500">
                              {Math.round(pct)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400 dark:text-slate-500">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot className="border-t-2 border-slate-200 dark:border-slate-700">
                <tr>
                  <td className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Total</td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">{totalAllocated}</td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">{totalUsed}</td>
                  <td className="px-4 py-3 text-right font-semibold text-teal-700 dark:text-teal-400">{totalRemaining}</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {usageOnlyBalances.length > 0 && (
        <div>
          <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">
            Other leave used · {year}
          </h2>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Leave type</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Days used</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {usageOnlyBalances.map((b) => {
                  const typeName = leaveTypes.find((t) => t.id === b.leave_type_id)?.name ?? "—";
                  return (
                    <tr key={b.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                      <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{typeName}</td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{b.used_days}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Leave request history for the period */}
      <div>
        <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100">
          Requests · {year}
        </h2>
        {periodRequests.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No leave requests for this period.
          </p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Period</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Days</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Reason</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Note</th>
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
                        {fmtDate(req.start_date)}
                        {req.start_date !== req.end_date && <> – {fmtDate(req.end_date)}</>}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{req.total_days}</td>
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
