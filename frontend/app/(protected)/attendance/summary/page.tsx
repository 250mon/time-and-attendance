"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  cancelCorrection,
  createCorrection,
  fetchAttendanceDays,
  fetchCorrections,
  getApiErrorMessage,
} from "@/lib/api-client";
import type { AttendanceCorrectionRequest, AttendanceDay, AttendanceDayStatus } from "@/types";

const STATUS_LABELS: Record<AttendanceDayStatus, string> = {
  NOT_STARTED: "Not started",
  WORKING: "Working",
  COMPLETED: "Completed",
  ABSENT: "Absent",
  HOLIDAY: "Holiday",
  ON_LEAVE: "On leave",
};

const STATUS_COLORS: Record<AttendanceDayStatus, string> = {
  NOT_STARTED: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
  WORKING: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
  COMPLETED: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  ABSENT: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  HOLIDAY: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  ON_LEAVE: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
};

function fmtMins(mins: number): string {
  if (mins === 0) return "—";
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h > 0 ? `${h}h ${m > 0 ? `${m}m` : ""}`.trim() : `${m}m`;
}

function fmtDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

type CorrectionForm = {
  workDate: string;
  clockIn: string;
  clockOut: string;
  reason: string;
};

const EMPTY_FORM: CorrectionForm = { workDate: "", clockIn: "", clockOut: "", reason: "" };

export default function AttendanceSummaryPage() {
  const [days, setDays] = useState<AttendanceDay[]>([]);
  const [corrections, setCorrections] = useState<AttendanceCorrectionRequest[]>([]);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedDay, setExpandedDay] = useState<string | null>(null);
  const [form, setForm] = useState<CorrectionForm>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);

  function reload() {
    setLoading(true);
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - (period - 1));
    const sd = start.toISOString().slice(0, 10);
    const ed = end.toISOString().slice(0, 10);
    Promise.all([
      fetchAttendanceDays({ start_date: sd, end_date: ed }),
      fetchCorrections(),
    ])
      .then(([d, c]) => { setDays(d); setCorrections(c); })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load summary")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { reload(); }, [period]); // eslint-disable-line react-hooks/exhaustive-deps

  function correctionForDate(workDate: string) {
    return corrections.find((c) => c.work_date === workDate && (c.status === "PENDING" || c.status === "APPROVED"));
  }

  function openForm(day: AttendanceDay) {
    setExpandedDay(day.work_date);
    setForm({ ...EMPTY_FORM, workDate: day.work_date });
    setFormError(null);
  }

  function closeForm() {
    setExpandedDay(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setActing(true);
    setFormError(null);
    try {
      await createCorrection({
        work_date: form.workDate,
        corrected_clock_in: form.clockIn || null,
        corrected_clock_out: form.clockOut || null,
        reason: form.reason,
      });
      closeForm();
      reload();
    } catch (err) {
      setFormError(getApiErrorMessage(err, "Could not submit correction"));
    } finally {
      setActing(false);
    }
  }

  async function handleCancel(correctionId: string) {
    setActing(true);
    try {
      await cancelCorrection(correctionId);
      reload();
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Could not cancel correction"));
    } finally {
      setActing(false);
    }
  }

  const totalWorked = days.reduce((s, d) => s + d.worked_minutes, 0);
  const totalOvertime = days.reduce((s, d) => s + d.overtime_minutes, 0);
  const totalLate = days.filter((d) => d.late_minutes > 0).length;
  const totalAbsent = days.filter((d) => d.status === "ABSENT").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Attendance Summary</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Your calculated attendance by day.</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Show last</label>
          <select
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
          <Link href="/attendance/my" className="text-sm font-medium text-teal-700 hover:underline dark:text-teal-400">
            Raw punches →
          </Link>
        </div>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

      {!loading && days.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Worked", value: fmtMins(totalWorked) },
            { label: "Overtime", value: fmtMins(totalOvertime) },
            { label: "Late days", value: String(totalLate) },
            { label: "Absent days", value: String(totalAbsent) },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">{label}</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">{value}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : days.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No attendance records in the selected period.</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Date</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Worked</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Regular</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">OT</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Late</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Early out</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Correction</th>
              </tr>
            </thead>
            <tbody>
              {days.map((day) => {
                const existing = correctionForDate(day.work_date);
                const isExpanded = expandedDay === day.work_date;
                const isToday = day.work_date === new Date().toISOString().slice(0, 10);

                return (
                  <>
                    <tr key={day.id} className="divide-y divide-slate-100 hover:bg-slate-50 dark:divide-slate-800 dark:hover:bg-slate-800">
                      <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{fmtDate(day.work_date)}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[day.status]}`}>
                          {STATUS_LABELS[day.status]}
                        </span>
                        {day.is_locked && <span className="ml-1 text-xs text-slate-400 dark:text-slate-500">🔒</span>}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{fmtMins(day.worked_minutes)}</td>
                      <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">{fmtMins(day.regular_minutes)}</td>
                      <td className="px-4 py-3 text-right">
                        {day.overtime_minutes > 0
                          ? <span className="text-amber-600 dark:text-amber-400">{fmtMins(day.overtime_minutes)}</span>
                          : <span className="text-slate-400 dark:text-slate-500">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {day.late_minutes > 0
                          ? <span className="text-rose-600 dark:text-rose-400">{fmtMins(day.late_minutes)}</span>
                          : <span className="text-slate-400 dark:text-slate-500">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {day.early_leave_minutes > 0
                          ? <span className="text-rose-600 dark:text-rose-400">{fmtMins(day.early_leave_minutes)}</span>
                          : <span className="text-slate-400 dark:text-slate-500">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {day.is_locked ? null : existing ? (
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-medium ${existing.status === "APPROVED" ? "text-teal-700 dark:text-teal-400" : "text-amber-600 dark:text-amber-400"}`}>
                              {existing.status === "APPROVED" ? "Approved" : "Pending"}
                            </span>
                            {existing.status === "PENDING" && (
                              <button
                                type="button"
                                disabled={acting}
                                onClick={() => handleCancel(existing.id)}
                                className="text-xs text-rose-600 hover:underline dark:text-rose-400"
                              >
                                Cancel
                              </button>
                            )}
                          </div>
                        ) : isToday ? null : (
                          <button
                            type="button"
                            onClick={() => (isExpanded ? closeForm() : openForm(day))}
                            className="text-xs font-medium text-teal-700 hover:underline dark:text-teal-400"
                          >
                            {isExpanded ? "Close" : "Request correction"}
                          </button>
                        )}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${day.id}-form`}>
                        <td colSpan={8} className="bg-slate-50 px-4 pb-4 pt-2 dark:bg-slate-800">
                          <form onSubmit={handleSubmit} className="space-y-3">
                            <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                              Correction for {fmtDate(day.work_date)}
                            </p>
                            <div className="flex flex-wrap gap-4">
                              <label className="flex flex-col gap-1 text-xs text-slate-600 dark:text-slate-400">
                                Corrected clock-in
                                <input
                                  type="time"
                                  value={form.clockIn}
                                  onChange={(e) => setForm((f) => ({ ...f, clockIn: e.target.value }))}
                                  className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                                />
                              </label>
                              <label className="flex flex-col gap-1 text-xs text-slate-600 dark:text-slate-400">
                                Corrected clock-out
                                <input
                                  type="time"
                                  value={form.clockOut}
                                  onChange={(e) => setForm((f) => ({ ...f, clockOut: e.target.value }))}
                                  className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                                />
                              </label>
                              <label className="flex flex-1 flex-col gap-1 text-xs text-slate-600 dark:text-slate-400">
                                Reason (required)
                                <input
                                  type="text"
                                  value={form.reason}
                                  onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
                                  placeholder="Briefly explain the correction"
                                  maxLength={500}
                                  className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                                />
                              </label>
                            </div>
                            {formError && <p className="text-xs text-rose-600 dark:text-rose-400">{formError}</p>}
                            <div className="flex gap-2">
                              <button
                                type="submit"
                                disabled={acting || !form.reason.trim() || (!form.clockIn && !form.clockOut)}
                                className="rounded bg-teal-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50 dark:bg-teal-600 dark:hover:bg-teal-700"
                              >
                                {acting ? "…" : "Submit"}
                              </button>
                              <button
                                type="button"
                                onClick={closeForm}
                                className="rounded border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700"
                              >
                                Cancel
                              </button>
                            </div>
                          </form>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
