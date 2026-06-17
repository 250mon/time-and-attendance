"use client";

import { useEffect, useState } from "react";

import { fetchClosings, getApiErrorMessage, lockMonth, unlockMonth } from "@/lib/api-client";
import { useAuth } from "@/components/AuthProvider";
import type { MonthlyClosing } from "@/types";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const CURRENT_YEAR = new Date().getFullYear();

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}

export default function SettingsPage() {
  const { user } = useAuth();
  const canManage = user?.role === "OWNER" || user?.role === "ADMIN";

  const [year, setYear] = useState(CURRENT_YEAR);
  const [closings, setClosings] = useState<MonthlyClosing[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function reload() {
    setLoading(true);
    fetchClosings({ year })
      .then(setClosings)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load closings")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { reload(); }, [year]); // eslint-disable-line react-hooks/exhaustive-deps

  function getClosing(month: number): MonthlyClosing | undefined {
    return closings.find((c) => c.year === year && c.month === month);
  }

  async function handleToggle(month: number, currentlyLocked: boolean) {
    const key = `${year}-${month}`;
    setActing(key);
    setErrorMessage(null);
    try {
      if (currentlyLocked) {
        await unlockMonth(year, month);
      } else {
        await lockMonth(year, month);
      }
      reload();
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Action failed"));
    } finally {
      setActing(null);
    }
  }

  const years = [CURRENT_YEAR - 2, CURRENT_YEAR - 1, CURRENT_YEAR, CURRENT_YEAR + 1];
  const today = new Date();
  const currentMonth = today.getMonth() + 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Settings</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Manage monthly period closings.</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Monthly Closings</h2>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>

        {!canManage && (
          <p className="mb-4 text-sm text-amber-600 dark:text-amber-400">
            Only Owners and Admins can lock or unlock months.
          </p>
        )}

        {errorMessage && <p className="mb-4 text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

        {loading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {MONTH_NAMES.map((name, i) => {
              const month = i + 1;
              const closing = getClosing(month);
              const isLocked = closing?.is_locked ?? false;
              const isFuture =
                year > today.getFullYear() ||
                (year === today.getFullYear() && month > currentMonth);
              const key = `${year}-${month}`;

              return (
                <div
                  key={month}
                  className={`rounded-lg border p-4 ${
                    isLocked
                      ? "border-rose-200 bg-rose-50 dark:border-rose-800 dark:bg-rose-950"
                      : isFuture
                      ? "border-slate-100 bg-slate-50 opacity-60 dark:border-slate-800 dark:bg-slate-900"
                      : "border-teal-200 bg-teal-50 dark:border-teal-800 dark:bg-teal-950"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{name}</p>
                      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                        {isLocked
                          ? `Locked ${fmtDate(closing?.locked_at ?? null)}`
                          : "Open"}
                      </p>
                    </div>
                    <span
                      className={`mt-0.5 rounded-full px-2 py-0.5 text-xs font-medium ${
                        isLocked
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300"
                          : "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300"
                      }`}
                    >
                      {isLocked ? "Locked" : "Open"}
                    </span>
                  </div>

                  {canManage && !isFuture && (
                    <button
                      type="button"
                      disabled={acting === key}
                      onClick={() => handleToggle(month, isLocked)}
                      className={`mt-3 w-full rounded-md px-3 py-1.5 text-xs font-semibold disabled:opacity-60 ${
                        isLocked
                          ? "border border-rose-300 text-rose-700 hover:bg-rose-100 dark:border-rose-700 dark:text-rose-400 dark:hover:bg-rose-900"
                          : "border border-slate-300 text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                      }`}
                    >
                      {acting === key ? "…" : isLocked ? "Unlock" : "Lock"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
