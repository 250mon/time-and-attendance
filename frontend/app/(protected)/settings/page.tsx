"use client";

import { useEffect, useRef, useState } from "react";

import {
  fetchClinic,
  fetchClosings,
  getApiErrorMessage,
  lockMonth,
  unlockMonth,
  updateClinic,
} from "@/lib/api-client";
import { useAuth } from "@/components/AuthProvider";
import type { Clinic, MonthlyClosing } from "@/types";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const CURRENT_YEAR = new Date().getFullYear();

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}

// ── Clinic Profile ────────────────────────────────────────────────────────────

function ClinicProfileSection() {
  const { user } = useAuth();
  const canEdit = user?.role === "OWNER" || user?.role === "ADMIN";

  const [clinic, setClinic] = useState<Clinic | null>(null);
  const [form, setForm] = useState({ name: "", timezone: "", address: "" });
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const savedTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchClinic()
      .then((c) => {
        setClinic(c);
        setForm({ name: c.name, timezone: c.timezone, address: c.address ?? "" });
      })
      .catch((e) => setError(getApiErrorMessage(e, "Unable to load clinic profile")));
  }, []);

  function handleChange(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setDirty(true);
    setSaved(false);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!dirty) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateClinic({
        name: form.name.trim(),
        timezone: form.timezone.trim(),
        address: form.address.trim() || null,
      });
      setClinic(updated);
      setDirty(false);
      setSaved(true);
      if (savedTimer.current) clearTimeout(savedTimer.current);
      savedTimer.current = setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to save clinic profile"));
    } finally {
      setSaving(false);
    }
  }

  if (!clinic) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">Clinic Profile</h2>
        {error
          ? <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>
          : <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-5">Clinic Profile</h2>

      {!canEdit && (
        <p className="mb-4 text-sm text-amber-600 dark:text-amber-400">
          Only Owners and Admins can edit clinic settings.
        </p>
      )}

      <form onSubmit={handleSave} className="space-y-4 max-w-lg">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Clinic name
          </label>
          <input
            type="text"
            value={form.name}
            disabled={!canEdit}
            onChange={(e) => handleChange("name", e.target.value)}
            required
            minLength={1}
            maxLength={255}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-60"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Timezone
          </label>
          <input
            type="text"
            value={form.timezone}
            disabled={!canEdit}
            onChange={(e) => handleChange("timezone", e.target.value)}
            placeholder="e.g. Asia/Seoul"
            required
            maxLength={64}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-60"
          />
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            IANA timezone identifier — used in all attendance and leave calculations.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Address <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <textarea
            value={form.address}
            disabled={!canEdit}
            onChange={(e) => handleChange("address", e.target.value)}
            rows={3}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-60"
          />
        </div>

        {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}

        {canEdit && (
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving || !dirty}
              className="rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
            {saved && (
              <span className="text-sm text-teal-600 dark:text-teal-400">Saved</span>
            )}
          </div>
        )}
      </form>
    </div>
  );
}

// ── Monthly Closings ──────────────────────────────────────────────────────────

function MonthlyClosingsSection() {
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
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Settings</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Manage clinic profile and monthly period closings.
        </p>
      </div>

      <ClinicProfileSection />
      <MonthlyClosingsSection />
    </div>
  );
}
