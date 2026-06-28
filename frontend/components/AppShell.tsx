"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";
import type { NavItem, UserRole } from "@/types";

const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/attendance", label: "Attendance" },
  { href: "/leave", label: "Leave" },
  {
    href: "/staff",
    label: "Staff",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
  {
    href: "/shifts",
    label: "Shifts",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
  { href: "/schedules", label: "Schedules" },
  {
    href: "/attendance/corrections",
    label: "Corrections",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
  {
    href: "/leave/requests",
    label: "Leave Requests",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
  {
    href: "/leave/types",
    label: "Leave Types",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
  {
    href: "/leave/balances",
    label: "Leave Balances",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
  { href: "/reports", label: "Reports" },
  { href: "/settings", label: "Settings", roles: ["OWNER", "ADMIN"] },
  {
    href: "/audit-log",
    label: "Audit Log",
    roles: ["OWNER", "ADMIN", "MANAGER"],
  },
];

function canViewNavItem(role: UserRole, item: NavItem) {
  if (!item.roles) {
    return true;
  }
  return item.roles.includes(role);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  const visibleNavItems = navItems.filter((item) => canViewNavItem(user.role, item));

  return (
    <div className="flex min-h-full flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-sm font-semibold text-teal-700 dark:text-teal-400">
              {user.clinic.name}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Signed in as {user.name} · {user.role}
            </p>
          </div>
          <button
            type="button"
            onClick={async () => {
              await logout();
              router.replace("/login");
            }}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-6xl flex-1 gap-6 px-6 py-8">
        <nav className="hidden w-48 shrink-0 md:block">
          <ul className="space-y-1">
            {visibleNavItems.map((item) => {
              const isActive = pathname.startsWith(item.href);

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`block rounded-md px-3 py-2 text-sm font-medium ${
                      isActive
                        ? "bg-teal-700 text-white dark:bg-teal-600"
                        : "text-slate-700 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
