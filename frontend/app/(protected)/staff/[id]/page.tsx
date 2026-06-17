"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/AuthProvider";
import {
  adjustLeaveBalance,
  fetchLeaveBalances,
  fetchLeaveTypes,
  fetchStaffMember,
  getApiErrorMessage,
  updateStaffMember,
} from "@/lib/api-client";
import { staffUpdateSchema, type StaffUpdateFormValues } from "@/lib/validation";
import type { LeaveBalance, LeaveType, User } from "@/types";

const CURRENT_YEAR = new Date().getFullYear();

const inputCls = "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";
const inputDisabledCls = "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-700";
const labelCls = "block text-sm font-medium text-slate-700 dark:text-slate-300";

export default function StaffDetailPage() {
  const params = useParams<{ id: string }>();
  const { canDeactivateStaff, canManageStaff, user: currentUser } = useAuth();
  const [staffMember, setStaffMember] = useState<User | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [addingTypeId, setAddingTypeId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<StaffUpdateFormValues>({
    resolver: zodResolver(staffUpdateSchema),
  });

  useEffect(() => {
    fetchStaffMember(params.id)
      .then((member) => {
        setStaffMember(member);
        reset({
          name: member.name,
          email: member.email,
          phone: member.phone ?? "",
          role: member.role,
          employment_type: member.employment_type,
          hire_date: member.hire_date ?? "",
          status: member.status,
        });
      })
      .catch((error) => {
        setErrorMessage(getApiErrorMessage(error, "Unable to load staff member"));
      })
      .finally(() => setLoading(false));
  }, [params.id, reset]);

  useEffect(() => {
    if (!canManageStaff) return;
    Promise.all([
      fetchLeaveTypes(),
      fetchLeaveBalances({ user_id: params.id, year: CURRENT_YEAR }),
    ])
      .then(([types, bals]) => {
        setLeaveTypes(types.filter((t) => t.active));
        setBalances(bals.filter((b) => b.year === CURRENT_YEAR));
      })
      .catch(() => {});
  }, [params.id, canManageStaff]);

  if (loading) {
    return <p className="text-sm text-slate-600 dark:text-slate-400">Loading staff member...</p>;
  }

  if (!staffMember) {
    return <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage ?? "Staff not found"}</p>;
  }

  const canEditRole = currentUser?.role === "OWNER";

  const assignedTypeIds = new Set(balances.map((b) => b.leave_type_id));
  const unassignedTypes = leaveTypes.filter((lt) => !assignedTypeIds.has(lt.id));

  async function handleAddLeaveType(leaveTypeId: string) {
    setAddingTypeId(leaveTypeId);
    try {
      const newBalance = await adjustLeaveBalance({
        user_id: params.id,
        leave_type_id: leaveTypeId,
        year: CURRENT_YEAR,
        delta_days: 0,
        reason: "Leave type added from staff profile",
      });
      setBalances((prev) => [...prev, newBalance]);
    } catch {
      // silently ignore — balance page can be used for manual setup
    } finally {
      setAddingTypeId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/staff" className="text-sm text-teal-700 hover:underline dark:text-teal-400">
          Back to staff
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{staffMember.name}</h1>
      </div>

      <form
        className="max-w-2xl space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        onSubmit={handleSubmit(async (values) => {
          setErrorMessage(null);
          try {
            const updated = await updateStaffMember(params.id, {
              name: values.name,
              email: values.email,
              phone: values.phone || null,
              role: values.role,
              employment_type: values.employment_type,
              hire_date: values.hire_date || null,
              status: values.status,
            });
            setStaffMember(updated);
          } catch (error) {
            setErrorMessage(getApiErrorMessage(error, "Unable to update staff member"));
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
          </div>

          <div>
            <label className={labelCls}>Phone</label>
            <input className={inputCls} {...register("phone")} />
          </div>

          <div>
            <label className={labelCls}>Role</label>
            <select
              className={inputDisabledCls}
              disabled={!canEditRole}
              {...register("role")}
            >
              <option value="STAFF">Staff</option>
              <option value="MANAGER">Manager</option>
              <option value="ADMIN">Admin</option>
              <option value="OWNER">Owner</option>
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

          <div>
            <label className={labelCls}>Status</label>
            <select
              className={inputDisabledCls}
              disabled={!canDeactivateStaff}
              {...register("status")}
            >
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
              <option value="TERMINATED">Terminated</option>
            </select>
          </div>
        </div>

        {errorMessage ? (
          <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
        >
          {isSubmitting ? "Saving..." : "Save changes"}
        </button>
      </form>

      {canManageStaff && leaveTypes.length > 0 && (
        <div className="max-w-2xl space-y-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div>
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Assigned leave types
            </h2>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              To adjust allocations or view other years, use the Leave page.
            </p>
          </div>

          {balances.length > 0 && (
            <div className="space-y-1">
              {balances.map((b) => {
                const lt = leaveTypes.find((t) => t.id === b.leave_type_id);
                return (
                  <div
                    key={b.id}
                    className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5 dark:border-slate-700"
                  >
                    <span className="flex-1 text-sm text-slate-800 dark:text-slate-100">
                      {lt?.name ?? "Unknown"}
                    </span>
                    {lt?.tenure_based ? (
                      <span className="rounded-full bg-teal-50 px-2 py-0.5 text-xs font-medium text-teal-700 dark:bg-teal-900/40 dark:text-teal-400">
                        Auto
                      </span>
                    ) : null}
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {b.remaining_days} / {b.balance_days} days
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {unassignedTypes.length > 0 && (
            <div className="space-y-2 border-t border-slate-200 pt-3 dark:border-slate-700">
              <p className="text-xs font-medium text-slate-600 dark:text-slate-400">Not yet assigned</p>
              {unassignedTypes.map((lt) => (
                <div
                  key={lt.id}
                  className="flex items-center gap-3 rounded-lg border border-dashed border-slate-300 px-3 py-2 dark:border-slate-600"
                >
                  <span className="flex-1 text-sm text-slate-600 dark:text-slate-400">{lt.name}</span>
                  {lt.tenure_based ? (
                    <span className="text-xs text-slate-400 dark:text-slate-500">Auto from hire date</span>
                  ) : (
                    <span className="text-xs text-slate-400 dark:text-slate-500">
                      {lt.default_days_per_year ?? 0} days/year
                    </span>
                  )}
                  <button
                    type="button"
                    disabled={addingTypeId === lt.id}
                    onClick={() => handleAddLeaveType(lt.id)}
                    className="rounded bg-teal-700 px-2.5 py-1 text-xs font-medium text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
                  >
                    {addingTypeId === lt.id ? "Adding…" : "Add"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {balances.length === 0 && unassignedTypes.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">No leave types configured.</p>
          )}
        </div>
      )}
    </div>
  );
}
