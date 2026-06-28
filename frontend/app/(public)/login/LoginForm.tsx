"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/AuthProvider";
import { fetchClinicBySlug, getApiErrorMessage } from "@/lib/api-client";
import { loginSchema, type LoginFormValues } from "@/lib/validation";

const SLUG_STORAGE_KEY = "lastClinicSlug";
const MULTI_TENANT = process.env.NEXT_PUBLIC_MULTI_TENANT_ENABLED === "true";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [clinicName, setClinicName] = useState<string | null>(null);
  const [slugState, setSlugState] = useState<"idle" | "checking" | "found" | "notfound">("idle");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { clinic_slug: "", email: "", password: "" },
  });

  // Pre-fill slug from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(SLUG_STORAGE_KEY);
    if (saved) setValue("clinic_slug", saved);
  }, [setValue]);

  // Live-validate the slug field
  const slugValue = watch("clinic_slug");
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    const slug = slugValue?.trim() ?? "";
    if (!slug) {
      setSlugState("idle");
      setClinicName(null);
      return;
    }

    setSlugState("checking");
    debounceRef.current = setTimeout(async () => {
      try {
        const clinic = await fetchClinicBySlug(slug);
        setClinicName(clinic.name);
        setSlugState("found");
      } catch {
        setClinicName(null);
        setSlugState("notfound");
      }
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [slugValue]);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-sm font-medium uppercase tracking-wide text-teal-700 dark:text-teal-400">
          ClinicTime
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">Sign in</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Use your clinic account to access attendance and leave tools.
        </p>
      </div>

      <form
        className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        onSubmit={handleSubmit(async (values) => {
          setErrorMessage(null);
          const slug = values.clinic_slug?.trim() || undefined;
          try {
            await login(values.email, values.password, slug);
            if (slug) localStorage.setItem(SLUG_STORAGE_KEY, slug);
            const nextPath = searchParams.get("next") ?? "/dashboard";
            router.replace(nextPath);
          } catch (error) {
            setErrorMessage(getApiErrorMessage(error, "Unable to sign in"));
          }
        })}
      >
        {/* Clinic slug */}
        <div>
          <label
            htmlFor="clinic_slug"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Clinic ID{" "}
            {!MULTI_TENANT && (
              <span className="font-normal text-slate-400">(optional for single-clinic)</span>
            )}
          </label>
          <input
            id="clinic_slug"
            type="text"
            autoComplete="organization"
            placeholder="e.g. seoul-dental"
            required={MULTI_TENANT}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
            {...register("clinic_slug")}
          />
          {/* Slug feedback */}
          {slugState === "checking" && (
            <p className="mt-1 text-xs text-slate-400">Checking…</p>
          )}
          {slugState === "found" && clinicName && (
            <p className="mt-1 text-xs text-teal-600 dark:text-teal-400">
              ✓ {clinicName}
            </p>
          )}
          {slugState === "notfound" && (
            <p className="mt-1 text-xs text-rose-500 dark:text-rose-400">
              Clinic not found
            </p>
          )}
          {errors.clinic_slug && (
            <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">
              {errors.clinic_slug.message}
            </p>
          )}
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{errors.email.message}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            {...register("password")}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">
              {errors.password.message}
            </p>
          )}
        </div>

        {errorMessage && (
          <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
        )}

        <button
          type="submit"
          disabled={isSubmitting || (MULTI_TENANT && slugState !== "found")}
          className="w-full rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
