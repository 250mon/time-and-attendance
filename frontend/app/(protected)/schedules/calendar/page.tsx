"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchSchedules, fetchStaff, fetchShifts, getApiErrorMessage } from "@/lib/api-client";
import type { Shift, StaffSchedule, User } from "@/types";

function addDays(date: Date, n: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

function toISO(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function startOfWeek(d: Date): Date {
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  return addDays(d, diff);
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const STATUS_COLORS: Record<string, string> = {
  SCHEDULED: "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-300",
  OFF: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
  HOLIDAY: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  CANCELLED: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
};

export default function SchedulesCalendarPage() {
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [schedules, setSchedules] = useState<StaffSchedule[]>([]);
  const [staff, setStaff] = useState<User[]>([]);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const weekEnd = addDays(weekStart, 6);
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  const shiftMap = Object.fromEntries(shifts.map((s) => [s.id, s]));

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchSchedules({ start_date: toISO(weekStart), end_date: toISO(weekEnd) }),
      fetchStaff(),
      fetchShifts(),
    ])
      .then(([s, u, sh]) => {
        setSchedules(s);
        setStaff(u);
        setShifts(sh);
      })
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load calendar")))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekStart]);

  function getCell(userId: string, dateStr: string): StaffSchedule | undefined {
    return schedules.find((s) => s.user_id === userId && s.work_date === dateStr);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Schedule Calendar</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Week of {toISO(weekStart)} – {toISO(weekEnd)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setWeekStart((w) => addDays(w, -7))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            ← Prev
          </button>
          <button
            type="button"
            onClick={() => setWeekStart(startOfWeek(new Date()))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Today
          </button>
          <button
            type="button"
            onClick={() => setWeekStart((w) => addDays(w, 7))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Next →
          </button>
          <Link
            href="/schedules"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            List view
          </Link>
        </div>
      </div>

      {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading calendar…</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="w-36 px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Staff</th>
                {weekDays.map((day, i) => (
                  <th key={i} className="px-3 py-3 text-center font-medium text-slate-600 dark:text-slate-400">
                    <div>{DAY_LABELS[i]}</div>
                    <div className="text-xs font-normal text-slate-400 dark:text-slate-500">{toISO(day).slice(5)}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {staff.length === 0 ? (
                <tr>
                  <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={8}>No staff found.</td>
                </tr>
              ) : (
                staff.map((member) => (
                  <tr key={member.id}>
                    <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">{member.name}</td>
                    {weekDays.map((day, i) => {
                      const cell = getCell(member.id, toISO(day));
                      const shiftName = cell?.shift_id ? (shiftMap[cell.shift_id]?.name ?? "—") : null;
                      return (
                        <td key={i} className="px-2 py-2 text-center">
                          {cell ? (
                            <span
                              className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[cell.status] ?? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"}`}
                            >
                              {shiftName ?? cell.status}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-300 dark:text-slate-600">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
