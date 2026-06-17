"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  clockIn,
  clockOut,
  fetchTodayStatus,
  getApiErrorMessage,
} from "@/lib/api-client";
import type { TodayStatus } from "@/types";

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function fmtShiftTime(t: string | null) {
  return t ? t.slice(0, 5) : "—";
}

const PUNCH_LABELS: Record<string, string> = {
  CLOCK_IN: "Clock In",
  CLOCK_OUT: "Clock Out",
  BREAK_START: "Break Start",
  BREAK_END: "Break End",
  MANUAL: "Manual",
};

export default function AttendanceTodayPage() {
  const [status, setStatus] = useState<TodayStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchTodayStatus()
      .then(setStatus)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load today's status")))
      .finally(() => setLoading(false));
  }, []);

  async function handleClockIn() {
    setActing(true);
    setErrorMessage(null);
    try {
      await clockIn();
      const updated = await fetchTodayStatus();
      setStatus(updated);
    } catch (e) {
      setErrorMessage(getApiErrorMessage(e, "Unable to clock in"));
    } finally {
      setActing(false);
    }
  }

  async function handleClockOut() {
    setActing(true);
    setErrorMessage(null);
    try {
      await clockOut();
      const updated = await fetchTodayStatus();
      setStatus(updated);
    } catch (e) {
      setErrorMessage(getApiErrorMessage(e, "Unable to clock out"));
    } finally {
      setActing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-64 items-center justify-center text-sm text-slate-500 dark:text-slate-400">
        Loading…
      </div>
    );
  }

  if (!status) {
    return <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage ?? "Unable to load status"}</p>;
  }

  const hasSchedule = status.schedule !== null;
  const scheduledStart = status.schedule?.scheduled_start ?? null;
  const scheduledEnd = status.schedule?.scheduled_end ?? null;
  const hasPunches = status.punches.length > 0;
  const missingPunchWarning =
    hasSchedule && !hasPunches && scheduledStart !== null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Today</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{status.work_date}</p>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/attendance/summary"
            className="text-sm font-medium text-teal-700 hover:underline dark:text-teal-400"
          >
            Summary →
          </Link>
          <Link
            href="/attendance/my"
            className="text-sm font-medium text-teal-700 hover:underline dark:text-teal-400"
          >
            History →
          </Link>
        </div>
      </div>

      {/* Status card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
          {/* Status indicator */}
          <div className="flex flex-col items-center gap-2">
            <div
              className={`flex h-20 w-20 items-center justify-center rounded-full text-2xl font-bold ${
                status.is_clocked_in
                  ? "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300"
                  : "bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500"
              }`}
            >
              {status.is_clocked_in ? "IN" : "OUT"}
            </div>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {status.is_clocked_in ? "Clocked In" : "Not Clocked In"}
            </span>
          </div>

          {/* Info */}
          <div className="flex-1 space-y-3">
            {hasSchedule ? (
              <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm dark:bg-slate-800">
                <p className="font-medium text-slate-700 dark:text-slate-300">Scheduled shift</p>
                <p className="mt-0.5 text-slate-500 dark:text-slate-400">
                  {fmtShiftTime(scheduledStart)} – {fmtShiftTime(scheduledEnd)}
                  {status.schedule?.scheduled_break_minutes
                    ? ` · ${status.schedule.scheduled_break_minutes} min break`
                    : ""}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400 dark:text-slate-500">No shift scheduled for today.</p>
            )}

            {status.last_punch && (
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Last punch:{" "}
                <span className="font-medium">
                  {PUNCH_LABELS[status.last_punch.punch_type]} at{" "}
                  {fmtTime(status.last_punch.punched_at)}
                </span>
              </p>
            )}

            {missingPunchWarning && (
              <p className="rounded-md bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                You have a scheduled shift but haven&apos;t clocked in yet.
              </p>
            )}
          </div>

          {/* Action button */}
          <div className="shrink-0">
            {status.is_clocked_in ? (
              <button
                type="button"
                disabled={acting}
                onClick={handleClockOut}
                className="rounded-lg bg-rose-600 px-8 py-3 text-sm font-semibold text-white shadow hover:bg-rose-700 disabled:opacity-60"
              >
                {acting ? "…" : "Clock Out"}
              </button>
            ) : (
              <button
                type="button"
                disabled={acting}
                onClick={handleClockIn}
                className="rounded-lg bg-teal-700 px-8 py-3 text-sm font-semibold text-white shadow hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
              >
                {acting ? "…" : "Clock In"}
              </button>
            )}
          </div>
        </div>
      </div>

      {errorMessage && (
        <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
      )}

      {/* Today's punch list */}
      {hasPunches && (
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Today&apos;s punches</h2>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Time</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {status.punches.map((punch) => (
                  <tr key={punch.id}>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                      {PUNCH_LABELS[punch.punch_type] ?? punch.punch_type}
                    </td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{fmtTime(punch.punched_at)}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{punch.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
