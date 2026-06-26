"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import {
  createLeaveType,
  deactivateLeaveType,
  fetchLeaveTypes,
  getApiErrorMessage,
  updateLeaveType,
} from "@/lib/api-client";
import type { LeaveType } from "@/types";

const inputCls =
  "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";
const labelCls = "block text-sm font-medium text-slate-700 dark:text-slate-300";

const EMPTY_FORM = { name: "", default_days_per_year: "", requires_approval: true, tenure_based: false };

export default function LeaveTypesPage() {
  const { canManageStaff } = useAuth();
  const [types, setTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  useEffect(() => {
    fetchLeaveTypes(true)
      .then(setTypes)
      .catch((e) => setErrorMessage(getApiErrorMessage(e, "Unable to load leave types")))
      .finally(() => setLoading(false));
  }, []);

  if (!canManageStaff) {
    return (
      <PlaceholderPage
        title="Leave Types"
        description="You do not have permission to manage leave types."
      />
    );
  }

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setShowForm(false);
    setErrorMessage(null);
  }

  function startEdit(lt: LeaveType) {
    setForm({
      name: lt.name,
      default_days_per_year: lt.default_days_per_year != null ? String(lt.default_days_per_year) : "",
      requires_approval: lt.requires_approval,
      tenure_based: lt.tenure_based,
    });
    setEditingId(lt.id);
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMessage(null);
    const payload = {
      name: form.name.trim(),
      default_days_per_year: form.default_days_per_year !== "" ? Number(form.default_days_per_year) : null,
      requires_approval: form.requires_approval,
      tenure_based: form.tenure_based,
    };
    try {
      if (editingId) {
        const updated = await updateLeaveType(editingId, payload);
        setTypes((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      } else {
        const created = await createLeaveType(payload);
        setTypes((prev) => [...prev, created]);
      }
      resetForm();
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Unable to save leave type"));
    }
  }

  async function handleDeactivate(id: string) {
    setErrorMessage(null);
    try {
      const updated = await deactivateLeaveType(id);
      setTypes((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Unable to deactivate leave type"));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Leave Types</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Define leave categories. Annual leave is calculated from hire date; other types may
            limit how many days can be requested at once.
          </p>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
          >
            Add leave type
          </button>
        )}
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="max-w-lg space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <h2 className="font-medium text-slate-900 dark:text-slate-100">
            {editingId ? "Edit leave type" : "New leave type"}
          </h2>

          <div>
            <label className={labelCls}>Name</label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Annual Leave"
              className={inputCls}
            />
          </div>

          <div>
            <label className={labelCls}>Max days per request</label>
            <input
              type="number"
              min={1}
              disabled={form.tenure_based}
              value={form.default_days_per_year}
              onChange={(e) => setForm((f) => ({ ...f, default_days_per_year: e.target.value }))}
              placeholder={form.tenure_based ? "Not used for annual leave" : "Leave blank for no limit"}
              className={inputCls}
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {form.tenure_based
                ? "Annual entitlement is computed from hire date, not this field."
                : "Maximum duration of a single leave request. Usage is tracked without a yearly pool."}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              id="requires-approval"
              type="checkbox"
              checked={form.requires_approval}
              onChange={(e) => setForm((f) => ({ ...f, requires_approval: e.target.checked }))}
              className="h-4 w-4 rounded border-slate-300 text-teal-700 dark:border-slate-600"
            />
            <label htmlFor="requires-approval" className="text-sm text-slate-700 dark:text-slate-300">
              Requires manager approval
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input
              id="tenure-based"
              type="checkbox"
              checked={form.tenure_based}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  tenure_based: e.target.checked,
                  default_days_per_year: e.target.checked ? "" : f.default_days_per_year,
                }))
              }
              className="h-4 w-4 rounded border-slate-300 text-teal-700 dark:border-slate-600"
            />
            <label htmlFor="tenure-based" className="text-sm text-slate-700 dark:text-slate-300">
              Tenure-based allocation (LSA Art. 60 — days calculated from hire date)
            </label>
          </div>

          {errorMessage && <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}

          <div className="flex gap-2">
            <button
              type="submit"
              className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
            >
              {editingId ? "Save changes" : "Create"}
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
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Max / request</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Tracking</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Approval</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={6}>
                  Loading…
                </td>
              </tr>
            ) : types.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={6}>
                  No leave types defined yet.
                </td>
              </tr>
            ) : (
              types.map((lt) => (
                <tr key={lt.id} className={lt.active ? "" : "opacity-50"}>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{lt.name}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lt.tenure_based
                      ? "—"
                      : lt.default_days_per_year != null
                        ? lt.default_days_per_year
                        : "No limit"}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lt.tenure_based ? (
                      <span className="inline-flex items-center rounded-full bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-700 dark:bg-teal-900 dark:text-teal-300">
                        Annual allocation
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        Usage only
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lt.requires_approval ? "Required" : "Not required"}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lt.active ? "Active" : "Inactive"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => startEdit(lt)}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                      >
                        Edit
                      </button>
                      {lt.active && (
                        <button
                          type="button"
                          onClick={() => handleDeactivate(lt.id)}
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
