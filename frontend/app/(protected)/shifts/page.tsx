"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import {
  createShift,
  deactivateShift,
  fetchShifts,
  getApiErrorMessage,
  updateShift,
} from "@/lib/api-client";
import type { Shift } from "@/types";

const inputCls = "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";
const labelCls = "block text-sm font-medium text-slate-700 dark:text-slate-300";

function fmtTime(t: string) {
  return t.slice(0, 5);
}

export default function ShiftsPage() {
  const { canManageStaff } = useAuth();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    start_time: "09:00",
    end_time: "18:00",
    break_minutes: 60,
    crosses_midnight: false,
  });

  useEffect(() => {
    fetchShifts()
      .then(setShifts)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load shifts")))
      .finally(() => setLoading(false));
  }, []);

  if (!canManageStaff) {
    return <PlaceholderPage title="Shifts" description="You do not have permission to manage shifts." />;
  }

  function resetForm() {
    setForm({ name: "", start_time: "09:00", end_time: "18:00", break_minutes: 60, crosses_midnight: false });
    setEditingId(null);
    setShowForm(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMessage(null);
    const payload = {
      name: form.name,
      start_time: form.start_time + ":00",
      end_time: form.end_time + ":00",
      break_minutes: Number(form.break_minutes),
      crosses_midnight: form.crosses_midnight,
    };
    try {
      if (editingId) {
        const updated = await updateShift(editingId, payload);
        setShifts((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      } else {
        const created = await createShift(payload);
        setShifts((prev) => [...prev, created]);
      }
      resetForm();
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "Unable to save shift"));
    }
  }

  function startEdit(shift: Shift) {
    setForm({
      name: shift.name,
      start_time: shift.start_time.slice(0, 5),
      end_time: shift.end_time.slice(0, 5),
      break_minutes: shift.break_minutes,
      crosses_midnight: shift.crosses_midnight,
    });
    setEditingId(shift.id);
    setShowForm(true);
  }

  async function handleDeactivate(id: string) {
    try {
      const updated = await deactivateShift(id);
      setShifts((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "Unable to deactivate shift"));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Shifts</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Define reusable shift templates.</p>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
          >
            Add shift
          </button>
        )}
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="max-w-2xl space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <h2 className="font-medium text-slate-900 dark:text-slate-100">{editingId ? "Edit shift" : "New shift"}</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className={labelCls}>Name</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label className={labelCls}>Start time</label>
              <input
                type="time"
                required
                value={form.start_time}
                onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label className={labelCls}>End time</label>
              <input
                type="time"
                required
                value={form.end_time}
                onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
                className={inputCls}
              />
            </div>
            <div>
              <label className={labelCls}>Break (minutes)</label>
              <input
                type="number"
                min={0}
                value={form.break_minutes}
                onChange={(e) => setForm((f) => ({ ...f, break_minutes: Number(e.target.value) }))}
                className={inputCls}
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                id="crosses-midnight"
                type="checkbox"
                checked={form.crosses_midnight}
                onChange={(e) => setForm((f) => ({ ...f, crosses_midnight: e.target.checked }))}
                className="h-4 w-4 rounded border-slate-300 text-teal-700 dark:border-slate-600"
              />
              <label htmlFor="crosses-midnight" className="text-sm text-slate-700 dark:text-slate-300">
                Crosses midnight
              </label>
            </div>
          </div>
          {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}
          <div className="flex gap-2">
            <button
              type="submit"
              className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
            >
              {editingId ? "Save changes" : "Create shift"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {errorMessage && !showForm && (
        <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
          <thead className="bg-slate-50 dark:bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Name</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Hours</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Break</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={5}>Loading shifts...</td>
              </tr>
            ) : shifts.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={5}>No shifts defined yet.</td>
              </tr>
            ) : (
              shifts.map((shift) => (
                <tr key={shift.id} className={shift.active ? "" : "opacity-50"}>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{shift.name}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {fmtTime(shift.start_time)} – {fmtTime(shift.end_time)}
                    {shift.crosses_midnight && (
                      <span className="ml-1 text-xs text-slate-500 dark:text-slate-400">(+1)</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{shift.break_minutes} min</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {shift.active ? "Active" : "Inactive"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => startEdit(shift)}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                      >
                        Edit
                      </button>
                      {shift.active && (
                        <button
                          type="button"
                          onClick={() => handleDeactivate(shift.id)}
                          className="rounded-md border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 dark:border-rose-800 dark:text-rose-400 dark:hover:bg-rose-950"
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
