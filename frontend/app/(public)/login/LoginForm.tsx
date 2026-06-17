"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/AuthProvider";
import { getApiErrorMessage } from "@/lib/api-client";
import { loginSchema, type LoginFormValues } from "@/lib/validation";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

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
          try {
            await login(values.email, values.password);
            const nextPath = searchParams.get("next") ?? "/dashboard";
            router.replace(nextPath);
          } catch (error) {
            setErrorMessage(getApiErrorMessage(error, "Unable to sign in"));
          }
        })}
      >
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
          {errors.email ? (
            <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{errors.email.message}</p>
          ) : null}
        </div>

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
          {errors.password ? (
            <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">
              {errors.password.message}
            </p>
          ) : null}
        </div>

        {errorMessage ? (
          <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
