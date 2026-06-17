"use client";

import { useAuth } from "@/components/AuthProvider";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <p className="text-sm font-medium uppercase tracking-wide text-teal-700 dark:text-teal-400">
        Dashboard
      </p>
      <h1 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
        Welcome back, {user?.name}
      </h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-400">
        You are signed in as {user?.role}. Attendance, leave, and reporting
        workflows will appear here in later phases.
      </p>

      <dl className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <dt className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Email</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">{user?.email}</dd>
        </div>
        <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <dt className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Status</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">{user?.status}</dd>
        </div>
      </dl>
    </section>
  );
}
