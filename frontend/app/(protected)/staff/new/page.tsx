"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/AuthProvider";
import { adjustLeaveBalance, createStaffMember, fetchLeaveTypes, getApiErrorMessage } from "@/lib/api-client";
import { staffCreateSchema, type StaffCreateFormValues } from "@/lib/validation";
import type { LeaveType } from "@/types";

const CURRENT_YEAR = new Date().getFullYear();

const inputCls =
  "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";
const labelCls = "block text-sm font-medium text-slate-700 dark:text-slate-300";

export default function NewStaffPage() {
  const router = useRouter();
  const { canManageStaff, user } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [selectedLeaveTypes, setSelectedLeaveTypes] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchLeaveTypes()
      .then((types) => {
        const active = types.filter((t) => t.active);
        setLeaveTypes(active);
        setSelectedLeaveTypes(new Set(active.map((t) => t.id)));
      })
      .catch(() => {});
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<StaffCreateFormValues>({
    resolver: zodResolver(staffCreateSchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      password: "",
      role: "STAFF",
      employment_type: "FULL_TIME",
      hire_date: "",
    },
  });

  if (!canManageStaff) {
    return (
      <p className="text-sm text-rose-600 dark:text-rose-400">You do not have permission to add staff.</p>
    );
  }

  function toggleLeaveType(id: string) {
    setSelectedLeaveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/staff" className="text-sm text-teal-700 hover:underline dark:text-teal-400">
          Back to staff
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">Add staff member</h1>
      </div>

      <form
        className="max-w-2xl space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        onSubmit={handleSubmit(async (values) => {
          setErrorMessage(null);
          try {
            const created = await createStaffMember({
              name: values.name,
              email: values.email,
              phone: values.phone || null,
              password: values.password,
              role: values.role,
              employment_type: values.employment_type,
              hire_date: values.hire_date || null,
            });

            // Initialize leave balances for each selected type.
            // delta_days=0 triggers get_or_create_balance without changing the allocation.
            await Promise.allSettled(
              [...selectedLeaveTypes].map((leave_type_id) =>
                adjustLeaveBalance({
                  user_id: created.id,
                  leave_type_id,
                  year: CURRENT_YEAR,
                  delta_days: 0,
                  reason: "Initial allocation on staff creation",
                })
              )
            );

            router.push(`/staff/${created.id}`);
          } catch (error) {
            setErrorMessage(getApiErrorMessage(error, "Unable to create staff member"));
          }
        })}
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className={labelCls}>Name</label>
            <input className={inputCls} {...register("name")} />
            {errors.name ? (
              <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{errors.name.message}</p>
            ) : null}
          </div>

          <div>
            <label className={labelCls}>Email</label>
            <input type="email" className={inputCls} {...register("email")} />
            {errors.email ? (
              <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{errors.email.message}</p>
            ) : null}
          </div>

          <div>
            <label className={labelCls}>Phone</label>
            <input className={inputCls} {...register("phone")} />
          </div>

          <div>
            <label className={labelCls}>Temporary password</label>
            <input type="password" className={inputCls} {...register("password")} />
            {errors.password ? (
              <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{errors.password.message}</p>
            ) : null}
          </div>

          <div>
            <label className={labelCls}>Role</label>
            <select className={inputCls} {...register("role")}>
              <option value="STAFF">Staff</option>
              <option value="MANAGER">Manager</option>
              {user?.role === "OWNER" ? (
                <>
                  <option value="ADMIN">Admin</option>
                  <option value="OWNER">Owner</option>
                </>
              ) : null}
            </select>
          </div>

          <div>
            <label className={labelCls}>Employment type</label>
            <select className={inputCls} {...register("employment_type")}>
              <option value="FULL_TIME">Full time</option>
              <option value="PART_TIME">Part time</option>
              <option value="CONTRACT">Contract</option>
              <option value="TEMPORARY">Temporary</option>
            </select>
          </div>

          <div>
            <label className={labelCls}>Hire date</label>
            <input type="date" className={inputCls} {...register("hire_date")} />
          </div>
        </div>

        {leaveTypes.length > 0 && (
          <div className="space-y-3 border-t border-slate-200 pt-5 dark:border-slate-700">
            <div>
              <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Leave allocation for {CURRENT_YEAR}</h2>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Select which leave types to assign. Deselected types can be added later from the staff profile.
              </p>
            </div>
            <div className="space-y-2">
              {leaveTypes.map((lt) => (
                <label
                  key={lt.id}
                  className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  <input
                    type="checkbox"
                    checked={selectedLeaveTypes.has(lt.id)}
                    onChange={() => toggleLeaveType(lt.id)}
                    className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span className="flex-1 text-sm text-slate-800 dark:text-slate-100">{lt.name}</span>
                  {lt.tenure_based ? (
                    <span className="rounded-full bg-teal-50 px-2 py-0.5 text-xs font-medium text-teal-700 dark:bg-teal-900/40 dark:text-teal-400">
                      Auto from hire date
                    </span>
                  ) : (
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {lt.default_days_per_year ?? 0} days/year
                    </span>
                  )}
                </label>
              ))}
            </div>
          </div>
        )}

        {errorMessage ? (
          <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
        >
          {isSubmitting ? "Creating..." : "Create staff member"}
        </button>
      </form>
    </div>
  );
}
