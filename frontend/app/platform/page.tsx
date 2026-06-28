"use client";

import React, { useEffect, useRef, useState } from "react";

import {
  activatePlatformClinic,
  createPlatformClinic,
  fetchPlatformClinics,
  fetchPlatformMetrics,
  getApiErrorMessage,
  suspendPlatformClinic,
  updatePlatformClinic,
} from "@/lib/api-client";
import type { ClinicCreateInput, PlatformClinic, PlatformClinicUpdateInput, PlatformMetrics } from "@/types";

const TOKEN_KEY = "platformAdminToken";

function StatusBadge({ status }: { status: "ACTIVE" | "SUSPENDED" }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        status === "ACTIVE"
          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
          : "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300"
      }`}
    >
      {status}
    </span>
  );
}

const EMPTY_FORM: ClinicCreateInput = {
  name: "", slug: "", timezone: "Asia/Seoul", address: "",
  owner_name: "", owner_email: "", owner_password: "",
};

function CreateClinicForm({
  token,
  onCreated,
}: {
  token: string;
  onCreated: (clinic: PlatformClinic) => void;
}) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ClinicCreateInput>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set(field: keyof ClinicCreateInput, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createPlatformClinic(token, {
        ...form,
        address: form.address?.trim() || null,
      });
      onCreated(created);
      setForm(EMPTY_FORM);
      setOpen(false);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to create clinic"));
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
      >
        + New clinic
      </button>
    );
  }

  const field = (label: string, key: keyof ClinicCreateInput, opts?: { type?: string; placeholder?: string; required?: boolean }) => (
    <div>
      <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
        {label}{opts?.required !== false && <span className="text-rose-500 ml-0.5">*</span>}
      </label>
      <input
        type={opts?.type ?? "text"}
        value={form[key] as string}
        onChange={(e) => set(key, e.target.value)}
        placeholder={opts?.placeholder}
        required={opts?.required !== false}
        className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
      />
    </div>
  );

  return (
    <div className="rounded-xl border border-teal-200 bg-teal-50 p-5 dark:border-teal-800 dark:bg-teal-950/30">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Create new clinic</h3>
        <button onClick={() => { setOpen(false); setForm(EMPTY_FORM); setError(null); }}
          className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">Cancel</button>
      </div>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {field("Clinic name", "name", { placeholder: "Seoul Dental Clinic" })}
        {field("Slug", "slug", { placeholder: "seoul-dental" })}
        {field("Timezone", "timezone", { placeholder: "Asia/Seoul" })}
        {field("Address", "address", { placeholder: "123 Gangnam-daero, Seoul", required: false })}
        {field("Owner name", "owner_name", { placeholder: "Dr. Kim" })}
        {field("Owner email", "owner_email", { type: "email", placeholder: "kim@example.com" })}
        {field("Owner password", "owner_password", { type: "password", placeholder: "min 8 chars" })}
        <div className="sm:col-span-2">
          {error && <p className="mb-2 text-xs text-rose-600 dark:text-rose-400">{error}</p>}
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50 dark:bg-teal-600"
          >
            {saving ? "Creating…" : "Create clinic"}
          </button>
        </div>
      </form>
    </div>
  );
}

function EditClinicForm({
  token,
  clinic,
  onSaved,
  onCancel,
}: {
  token: string;
  clinic: PlatformClinic;
  onSaved: (updated: PlatformClinic) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<PlatformClinicUpdateInput>({
    name: clinic.name,
    timezone: clinic.timezone,
    address: clinic.address ?? "",
    owner_name: "",
    owner_email: "",
    owner_password: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set(field: keyof PlatformClinicUpdateInput, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const patch: PlatformClinicUpdateInput = {};
    if (form.name !== clinic.name) patch.name = form.name;
    if (form.timezone !== clinic.timezone) patch.timezone = form.timezone;
    const addressVal = form.address?.trim() ?? null;
    const currentAddress = clinic.address ?? "";
    if (addressVal !== currentAddress) patch.address = addressVal || null;
    if (form.owner_name?.trim()) patch.owner_name = form.owner_name.trim();
    if (form.owner_email?.trim()) patch.owner_email = form.owner_email.trim();
    if (form.owner_password?.trim()) patch.owner_password = form.owner_password.trim();

    if (Object.keys(patch).length === 0) { onCancel(); return; }

    try {
      const updated = await updatePlatformClinic(token, clinic.id, patch);
      onSaved(updated);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to update clinic"));
    } finally {
      setSaving(false);
    }
  }

  const row = (label: string, key: keyof PlatformClinicUpdateInput, opts?: { type?: string; placeholder?: string }) => (
    <div>
      <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{label}</label>
      <input
        type={opts?.type ?? "text"}
        value={form[key] as string}
        onChange={(e) => set(key, e.target.value)}
        placeholder={opts?.placeholder}
        className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
      />
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-amber-50 dark:bg-amber-950/20 border-t border-amber-200 dark:border-amber-800">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-400 mb-3">
        Editing: {clinic.name} <span className="font-mono font-normal">({clinic.slug})</span>
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 mb-3">
        <p className="sm:col-span-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">Clinic profile</p>
        {row("Name", "name")}
        {row("Timezone", "timezone", { placeholder: "Asia/Seoul" })}
        {row("Address", "address", { placeholder: "leave blank to clear" })}
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <p className="sm:col-span-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">Owner account (leave blank to keep unchanged)</p>
        {row("Owner name", "owner_name")}
        {row("Owner email", "owner_email", { type: "email" })}
        {row("New password", "owner_password", { type: "password", placeholder: "min 8 chars" })}
      </div>
      {error && <p className="mt-3 text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      <div className="mt-3 flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-amber-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-amber-700 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
        <button type="button" onClick={onCancel} className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
          Cancel
        </button>
      </div>
    </form>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">{value}</p>
    </div>
  );
}

export default function PlatformAdminPage() {
  const [token, setToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [clinics, setClinics] = useState<PlatformClinic[]>([]);
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Restore token from sessionStorage on mount and auto-connect
  useEffect(() => {
    const saved = sessionStorage.getItem(TOKEN_KEY);
    if (saved) {
      setToken(saved);
      void load(saved);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load(t: string) {
    setLoadError(null);
    try {
      const [c, m] = await Promise.all([fetchPlatformClinics(t), fetchPlatformMetrics(t)]);
      setClinics(c);
      setMetrics(m);
      setConnected(true);
      sessionStorage.setItem(TOKEN_KEY, t);
    } catch (err) {
      setConnected(false);
      sessionStorage.removeItem(TOKEN_KEY);
      setLoadError(getApiErrorMessage(err, "Failed to connect — check your platform token"));
    }
  }

  async function toggleStatus(clinic: PlatformClinic) {
    setActionError(null);
    setPendingId(clinic.id);
    try {
      const updated =
        clinic.status === "ACTIVE"
          ? await suspendPlatformClinic(token, clinic.id)
          : await activatePlatformClinic(token, clinic.id);
      setClinics((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      setMetrics((prev) =>
        prev
          ? {
              ...prev,
              active_clinics:
                updated.status === "ACTIVE" ? prev.active_clinics + 1 : prev.active_clinics - 1,
              suspended_clinics:
                updated.status === "SUSPENDED"
                  ? prev.suspended_clinics + 1
                  : prev.suspended_clinics - 1,
            }
          : prev,
      );
    } catch (err) {
      setActionError(getApiErrorMessage(err, "Action failed"));
    } finally {
      setPendingId(null);
    }
  }

  function disconnect() {
    setConnected(false);
    setClinics([]);
    setMetrics(null);
    setToken("");
    sessionStorage.removeItem(TOKEN_KEY);
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Top bar */}
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <div>
            <span className="text-sm font-semibold text-teal-700 dark:text-teal-400">
              ClinicTime
            </span>
            <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">
              / Platform Admin
            </span>
          </div>
          {connected && (
            <button
              onClick={disconnect}
              className="text-xs text-slate-500 underline hover:text-slate-700 dark:hover:text-slate-300"
            >
              Disconnect
            </button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8 space-y-8">
        {/* Token entry */}
        {!connected && (
          <div className="mx-auto max-w-sm space-y-4">
            <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Platform Admin
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Enter the <code className="font-mono text-xs">PLATFORM_ADMIN_SECRET</code> to
              access platform controls.
            </p>
            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                void load(token);
              }}
            >
              <input
                ref={inputRef}
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Platform token"
                autoComplete="off"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              />
              {loadError && (
                <p className="text-xs text-rose-600 dark:text-rose-400">{loadError}</p>
              )}
              <button
                type="submit"
                disabled={!token}
                className="w-full rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-50 dark:bg-teal-600"
              >
                Connect
              </button>
            </form>
          </div>
        )}

        {/* Connected view */}
        {connected && (
          <>
            {/* Metrics */}
            {metrics && (
              <div>
                <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Platform Overview
                </h2>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <MetricCard label="Total Clinics" value={metrics.total_clinics} />
                  <MetricCard label="Active" value={metrics.active_clinics} />
                  <MetricCard label="Suspended" value={metrics.suspended_clinics} />
                  <MetricCard label="Total Users" value={metrics.total_users} />
                </div>
              </div>
            )}

            {/* Create clinic */}
            <CreateClinicForm
              token={token}
              onCreated={(created) => {
                setClinics((prev) => [...prev, created]);
                setMetrics((prev) =>
                  prev
                    ? { ...prev, total_clinics: prev.total_clinics + 1, active_clinics: prev.active_clinics + 1 }
                    : prev,
                );
              }}
            />

            {/* Clinic list */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Clinics
                </h2>
                <button
                  onClick={() => void load(token)}
                  className="text-xs text-teal-700 hover:underline dark:text-teal-400"
                >
                  Refresh
                </button>
              </div>

              {actionError && (
                <p className="mb-3 text-sm text-rose-600 dark:text-rose-400">{actionError}</p>
              )}

              {clinics.length === 0 ? (
                <p className="text-sm text-slate-500">No clinics found.</p>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                      <tr>
                        {["Name / Slug", "Status", "Users", "Timezone", "Created", "Actions"].map(
                          (h) => (
                            <th
                              key={h}
                              className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400"
                            >
                              {h}
                            </th>
                          ),
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-900">
                      {clinics.map((clinic) => (
                        <React.Fragment key={clinic.id}>
                          <tr className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 ${editingId === clinic.id ? "bg-amber-50/60 dark:bg-amber-950/10" : ""}`}>
                            <td className="px-4 py-3">
                              <p className="font-medium text-slate-900 dark:text-slate-100">
                                {clinic.name}
                              </p>
                              <p className="font-mono text-xs text-slate-400">{clinic.slug}</p>
                            </td>
                            <td className="px-4 py-3">
                              <StatusBadge status={clinic.status} />
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                              {clinic.user_count}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                              {clinic.timezone}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                              {new Date(clinic.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-3 text-right space-x-2">
                              <button
                                onClick={() => setEditingId(editingId === clinic.id ? null : clinic.id)}
                                className="rounded px-3 py-1 text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
                              >
                                {editingId === clinic.id ? "Close" : "Edit"}
                              </button>
                              <button
                                disabled={pendingId === clinic.id}
                                onClick={() => void toggleStatus(clinic)}
                                className={`rounded px-3 py-1 text-xs font-medium transition-opacity disabled:opacity-50 ${
                                  clinic.status === "ACTIVE"
                                    ? "bg-rose-100 text-rose-700 hover:bg-rose-200 dark:bg-rose-900/30 dark:text-rose-300"
                                    : "bg-emerald-100 text-emerald-700 hover:bg-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300"
                                }`}
                              >
                                {pendingId === clinic.id
                                  ? "…"
                                  : clinic.status === "ACTIVE"
                                    ? "Suspend"
                                    : "Activate"}
                              </button>
                            </td>
                          </tr>
                          {editingId === clinic.id && (
                            <tr>
                              <td colSpan={6} className="p-0">
                                <EditClinicForm
                                  token={token}
                                  clinic={clinic}
                                  onSaved={(updated) => {
                                    setClinics((prev) =>
                                      prev.map((c) => (c.id === updated.id ? updated : c)),
                                    );
                                    setEditingId(null);
                                  }}
                                  onCancel={() => setEditingId(null)}
                                />
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
