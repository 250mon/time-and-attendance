"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import {
  deleteSchedule,
  fetchSchedules,
  fetchShifts,
  fetchStaff,
  generateSchedules,
  getApiErrorMessage,
} from "@/lib/api-client";
import type { Shift, StaffSchedule, User } from "@/types";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function fmtTime(t: string | null) {
  return t ? t.slice(0, 5) : "—";
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function endOfMonth() {
  const d = new Date();
  d.setMonth(d.getMonth() + 1, 0);
  return d.toISOString().slice(0, 10);
}

export default function SchedulesPage() {
  const { canManageStaff } = useAuth();

  const [schedules, setSchedules] = useState<StaffSchedule[]>([]);
  const [staff, setStaff] = useState<User[]>([]);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [startDate, setStartDate] = useState(today());
  const [endDate, setEndDate] = useState(endOfMonth());
  const [filterUserId, setFilterUserId] = useState("");

  const [showGenerate, setShowGenerate] = useState(false);
  const [genForm, setGenForm] = useState({
    user_id: "",
    shift_id: "",
    start_date: today(),
    end_date: endOfMonth(),
    weekdays: [0, 1, 2, 3, 4] as number[],
  });

  const shiftMap = Object.fromEntries(shifts.map((s) => [s.id, s.name]));
  const staffMap = Object.fromEntries(staff.map((u) => [u.id, u.name]));

  useEffect(() => {
    const promises: Promise<unknown>[] = [
      fetchSchedules({ start_date: startDate, end_date: endDate, user_id: filterUserId || undefined })
        .then(setSchedules),
    ];
    if (canManageStaff) {
      promises.push(fetchStaff().then(setStaff));
      promises.push(fetchShifts().then(setShifts));
    }
    Promise.all(promises)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load schedules")))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function applyFilters() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchSchedules({
        start_date: startDate,
        end_date: endDate,
        user_id: filterUserId || undefined,
      });
      setSchedules(data);
    } catch (e) {
      setErrorMessage(getApiErrorMessage(e, "Unable to load schedules"));
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setErrorMessage(null);
    try {
      const created = await generateSchedules({
        user_id: genForm.user_id,
        shift_id: genForm.shift_id,
        start_date: genForm.start_date,
        end_date: genForm.end_date,
        weekdays: genForm.weekdays,
      });
      setSchedules((prev) => {
        const existingIds = new Set(prev.map((s) => s.id));
        return [...prev, ...created.filter((s) => !existingIds.has(s.id))];
      });
      setShowGenerate(false);
    } catch (e) {
      setErrorMessage(getApiErrorMessage(e, "Unable to generate schedules"));
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteSchedule(id);
      setSchedules((prev) => prev.filter((s) => s.id !== id));
    } catch (e) {
      setErrorMessage(getApiErrorMessage(e, "Unable to delete schedule"));
    }
  }

  function toggleWeekday(day: number) {
    setGenForm((f) => ({
      ...f,
      weekdays: f.weekdays.includes(day)
        ? f.weekdays.filter((d) => d !== day)
        : [...f.weekdays, day],
    }));
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Schedules</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">View and manage staff work schedules.</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/schedules/calendar"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Calendar view
          </Link>
          {canManageStaff && (
            <button
              type="button"
              onClick={() => setShowGenerate(true)}
              className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
            >
              Generate
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <div>
          <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">From</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">To</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
        </div>
        {canManageStaff && staff.length > 0 && (
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">Staff member</label>
            <select
              value={filterUserId}
              onChange={(e) => setFilterUserId(e.target.value)}
              className="mt-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            >
              <option value="">All staff</option>
              {staff.map((u) => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
          </div>
        )}
        <button
          type="button"
          onClick={applyFilters}
          className="rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 dark:bg-slate-600 dark:hover:bg-slate-500"
        >
          Apply
        </button>
      </div>

      {/* Generate form */}
      {showGenerate && (
        <form
          onSubmit={handleGenerate}
          className="space-y-4 rounded-xl border border-teal-200 bg-teal-50 p-6 dark:border-teal-800 dark:bg-teal-950"
        >
          <h2 className="font-medium text-slate-900 dark:text-slate-100">Generate schedules</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Staff member</label>
              <select
                required
                value={genForm.user_id}
                onChange={(e) => setGenForm((f) => ({ ...f, user_id: e.target.value }))}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">Select…</option>
                {staff.map((u) => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Shift</label>
              <select
                required
                value={genForm.shift_id}
                onChange={(e) => setGenForm((f) => ({ ...f, shift_id: e.target.value }))}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">Select…</option>
                {shifts.filter((s) => s.active).map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Start date</label>
              <input
                type="date"
                required
                value={genForm.start_date}
                onChange={(e) => setGenForm((f) => ({ ...f, start_date: e.target.value }))}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">End date</label>
              <input
                type="date"
                required
                value={genForm.end_date}
                onChange={(e) => setGenForm((f) => ({ ...f, end_date: e.target.value }))}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Days of week</label>
              <div className="mt-2 flex gap-2">
                {WEEKDAY_LABELS.map((label, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => toggleWeekday(i)}
                    className={`rounded-md px-3 py-1.5 text-xs font-medium ${
                      genForm.weekdays.includes(i)
                        ? "bg-teal-700 text-white dark:bg-teal-600"
                        : "border border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}
          <div className="flex gap-2">
            <button
              type="submit"
              className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
            >
              Generate schedules
            </button>
            <button
              type="button"
              onClick={() => setShowGenerate(false)}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {errorMessage && !showGenerate && (
        <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
          <thead className="bg-slate-50 dark:bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Date</th>
              {canManageStaff && (
                <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Staff</th>
              )}
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Shift</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Hours</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
              {canManageStaff && (
                <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Actions</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={6}>Loading schedules…</td>
              </tr>
            ) : schedules.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={6}>No schedules for the selected period.</td>
              </tr>
            ) : (
              schedules.map((s) => (
                <tr key={s.id}>
                  <td className="px-4 py-3 text-slate-900 dark:text-slate-100">{s.work_date}</td>
                  {canManageStaff && (
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{staffMap[s.user_id] ?? s.user_id.slice(0, 8)}</td>
                  )}
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {s.shift_id ? (shiftMap[s.shift_id] ?? "—") : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {fmtTime(s.scheduled_start)} – {fmtTime(s.scheduled_end)}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{s.status}</td>
                  {canManageStaff && (
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(s.id)}
                        className="rounded-md border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 dark:border-rose-800 dark:text-rose-400 dark:hover:bg-rose-950"
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
