"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/AuthProvider";
import { useBackendHealth } from "@/hooks/useBackendHealth";

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const backendStatus = useBackendHealth();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  if (loading || user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-600">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-6 py-12">
      <section className="w-full max-w-2xl rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-teal-700">
          ClinicTime
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Time and attendance for small clinics
        </h1>
        <p className="mt-4 text-sm leading-6 text-slate-600">
          Sign in to manage staff, track attendance, and handle leave requests.
        </p>

        <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              backendStatus === "ok"
                ? "bg-emerald-500"
                : backendStatus === "loading"
                  ? "bg-amber-400"
                  : "bg-rose-500"
            }`}
          />
          <span>
            Backend health:{" "}
            {backendStatus === "loading"
              ? "Checking..."
              : backendStatus === "ok"
                ? "Connected"
                : "Unavailable"}
          </span>
        </div>

        <div className="mt-8">
          <Link
            href="/login"
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
          >
            Sign in
          </Link>
        </div>
      </section>
    </div>
  );
}
