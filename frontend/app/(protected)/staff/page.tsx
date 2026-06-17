"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import {
  deactivateStaffMember,
  fetchStaff,
  getApiErrorMessage,
} from "@/lib/api-client";
import type { User } from "@/types";

export default function StaffPage() {
  const { canManageStaff, canDeactivateStaff } = useAuth();
  const [staff, setStaff] = useState<User[]>([]);
  const [loading, setLoading] = useState(canManageStaff);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!canManageStaff) {
      return;
    }

    let isMounted = true;

    fetchStaff()
      .then((members) => {
        if (isMounted) {
          setStaff(members);
        }
      })
      .catch((error) => {
        if (isMounted) {
          setErrorMessage(getApiErrorMessage(error, "Unable to load staff"));
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [canManageStaff]);

  if (!canManageStaff) {
    return (
      <PlaceholderPage
        title="Staff"
        description="You do not have permission to manage staff records."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Staff</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Manage clinic employees, roles, and account status.
          </p>
        </div>
        <Link
          href="/staff/new"
          className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-700"
        >
          Add staff
        </Link>
      </div>

      {errorMessage ? (
        <p className="text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
          <thead className="bg-slate-50 dark:bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Name</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Email</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Role</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-400">Status</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600 dark:text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {loading ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={5}>
                  Loading staff...
                </td>
              </tr>
            ) : staff.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-slate-500 dark:text-slate-400" colSpan={5}>
                  No staff members found.
                </td>
              </tr>
            ) : (
              staff.map((member) => (
                <tr key={member.id}>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                    {member.name}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{member.email}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{member.role}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{member.status}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/staff/${member.id}`}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                      >
                        Edit
                      </Link>
                      {canDeactivateStaff && member.status === "ACTIVE" ? (
                        <button
                          type="button"
                          className="rounded-md border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 dark:border-rose-800 dark:text-rose-400 dark:hover:bg-rose-950"
                          onClick={async () => {
                            try {
                              const updated = await deactivateStaffMember(member.id);
                              setStaff((current) =>
                                current.map((item) =>
                                  item.id === updated.id ? updated : item,
                                ),
                              );
                            } catch (error) {
                              setErrorMessage(
                                getApiErrorMessage(error, "Unable to deactivate staff"),
                              );
                            }
                          }}
                        >
                          Deactivate
                        </button>
                      ) : null}
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
