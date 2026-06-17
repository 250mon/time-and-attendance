"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchMyPunches, getApiErrorMessage } from "@/lib/api-client";
import type { AttendancePunch } from "@/types";

const PUNCH_LABELS: Record<string, string> = {
  CLOCK_IN: "Clock In",
  CLOCK_OUT: "Clock Out",
  BREAK_START: "Break Start",
  BREAK_END: "Break End",
  MANUAL: "Manual",
};

const PUNCH_COLORS: Record<string, string> = {
  CLOCK_IN: "text-teal-700 dark:text-teal-400",
  CLOCK_OUT: "text-slate-500 dark:text-slate-400",
  BREAK_START: "text-amber-600 dark:text-amber-400",
  BREAK_END: "text-amber-600 dark:text-amber-400",
  MANUAL: "text-indigo-600 dark:text-indigo-400",
};

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString([], {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function groupByDate(punches: AttendancePunch[]): [string, AttendancePunch[]][] {
  const map = new Map<string, AttendancePunch[]>();
  for (const p of punches) {
    const day = p.punched_at.slice(0, 10);
    const existing = map.get(day);
    if (existing) {
      existing.push(p);
    } else {
      map.set(day, [p]);
    }
  }
  return Array.from(map.entries());
}

export default function AttendanceMyPage() {
  const [punches, setPunches] = useState<AttendancePunch[]>([]);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchMyPunches(days)
      .then(setPunches)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load attendance history")))
      .finally(() => setLoading(false));
  }, [days]);

  const grouped = groupByDate(punches);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">My Attendance</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Your recent punch history.</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-600 dark:text-slate-400">Show last</label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
          <Link
            href="/attendance/summary"
            className="text-sm font-medium text-teal-700 hover:underline dark:text-teal-400"
          >
            Summary
          </Link>
          <Link
            href="/attendance"
            className="text-sm font-medium text-teal-700 hover:underline dark:text-teal-400"
          >
            ← Today
          </Link>
        </div>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : grouped.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No punch records in the selected period.</p>
      ) : (
        <div className="space-y-4">
          {grouped.map(([day, dayPunches]) => (
            <div
              key={day}
              className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900"
            >
              <div className="border-b border-slate-100 bg-slate-50 px-4 py-2 dark:border-slate-800 dark:bg-slate-800">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {fmtDate(dayPunches[0].punched_at)}
                </span>
                <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">
                  {dayPunches.length} punch{dayPunches.length !== 1 ? "es" : ""}
                </span>
              </div>
              <table className="min-w-full text-sm">
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {dayPunches.map((punch) => (
                    <tr key={punch.id}>
                      <td className={`px-4 py-2.5 font-medium ${PUNCH_COLORS[punch.punch_type] ?? "text-slate-700 dark:text-slate-300"}`}>
                        {PUNCH_LABELS[punch.punch_type] ?? punch.punch_type}
                      </td>
                      <td className="px-4 py-2.5 text-slate-700 dark:text-slate-300">{fmtTime(punch.punched_at)}</td>
                      <td className="px-4 py-2.5 text-slate-400 dark:text-slate-500">{punch.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
