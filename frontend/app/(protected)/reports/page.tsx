"use client";

import { useEffect, useState } from "react";

import {
  downloadReport,
  fetchAttendanceSummary,
  fetchLeaveSummaryReport,
  fetchMonthlyDetail,
  fetchStaff,
  getApiErrorMessage,
} from "@/lib/api-client";
import { useAuth } from "@/components/AuthProvider";
import type { User } from "@/types";

type ReportType = "attendance-summary" | "leave-summary" | "monthly-detail";

const CURRENT_YEAR = new Date().getFullYear();
const CURRENT_MONTH = new Date().getMonth() + 1;

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Column definitions per report type ──────────────────────────────────────

const COLUMNS: Record<ReportType, { key: string; label: string }[]> = {
  "attendance-summary": [
    { key: "user_name", label: "Staff" },
    { key: "total_records", label: "Records" },
    { key: "days_present", label: "Present" },
    { key: "days_absent", label: "Absent" },
    { key: "days_on_leave", label: "On Leave" },
    { key: "days_holiday", label: "Holiday" },
    { key: "worked_hours", label: "Worked (h)" },
    { key: "overtime_hours", label: "OT (h)" },
    { key: "late_minutes", label: "Late (min)" },
    { key: "early_leave_minutes", label: "Early Leave (min)" },
  ],
  "leave-summary": [
    { key: "user_name", label: "Staff" },
    { key: "leave_type_name", label: "Leave Type" },
    { key: "year", label: "Year" },
    { key: "balance_days", label: "Allocated" },
    { key: "used_days", label: "Used" },
    { key: "remaining_days", label: "Remaining" },
  ],
  "monthly-detail": [
    { key: "work_date", label: "Date" },
    { key: "user_name", label: "Staff" },
    { key: "status", label: "Status" },
    { key: "actual_clock_in", label: "Clock In" },
    { key: "actual_clock_out", label: "Clock Out" },
    { key: "worked_hours", label: "Worked (h)" },
    { key: "overtime_minutes", label: "OT (min)" },
    { key: "late_minutes", label: "Late (min)" },
    { key: "is_locked", label: "Locked" },
  ],
};

function fmtCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string" && value.includes("T")) {
    // datetime ISO string — show time part only
    const d = new Date(value);
    if (!isNaN(d.getTime())) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return String(value);
}

export default function ReportsPage() {
  const { user } = useAuth();
  const isManager = user?.role === "OWNER" || user?.role === "ADMIN" || user?.role === "MANAGER";

  const [reportType, setReportType] = useState<ReportType>("attendance-summary");
  const [staff, setStaff] = useState<User[]>([]);
  const [staffFilter, setStaffFilter] = useState("");
  const [year, setYear] = useState(CURRENT_YEAR);
  const [month, setMonth] = useState(CURRENT_MONTH);
  const [startDate, setStartDate] = useState(
    isoDate(new Date(CURRENT_YEAR, CURRENT_MONTH - 1, 1))
  );
  const [endDate, setEndDate] = useState(isoDate(new Date()));
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [generated, setGenerated] = useState(false);

  useEffect(() => {
    if (isManager) fetchStaff().then(setStaff).catch(() => {});
  }, [isManager]);

  async function handleGenerate() {
    setLoading(true);
    setErrorMessage(null);
    setRows([]);
    try {
      let data: Record<string, unknown>[] = [];
      const uid = staffFilter || undefined;
      if (reportType === "attendance-summary") {
        data = await fetchAttendanceSummary({ start_date: startDate, end_date: endDate, user_id: uid });
      } else if (reportType === "leave-summary") {
        data = await fetchLeaveSummaryReport({ year, user_id: uid });
      } else {
        data = await fetchMonthlyDetail({ year, month, user_id: uid });
      }
      setRows(data);
      setGenerated(true);
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Failed to generate report"));
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setErrorMessage(null);
    try {
      const uid = staffFilter || undefined;
      let blob: Blob;
      let filename: string;

      if (reportType === "attendance-summary") {
        blob = await downloadReport("/reports/attendance-summary", {
          start_date: startDate, end_date: endDate, user_id: uid,
        });
        filename = `attendance_summary_${startDate}_${endDate}.xlsx`;
      } else if (reportType === "leave-summary") {
        blob = await downloadReport("/reports/leave-summary", { year, user_id: uid });
        filename = `leave_summary_${year}.xlsx`;
      } else {
        blob = await downloadReport("/reports/monthly-detail", { year, month, user_id: uid });
        filename = `monthly_detail_${year}_${String(month).padStart(2, "0")}.xlsx`;
      }
      triggerDownload(blob, filename);
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err, "Download failed"));
    } finally {
      setDownloading(false);
    }
  }

  const columns = COLUMNS[reportType];
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  const years = [CURRENT_YEAR - 2, CURRENT_YEAR - 1, CURRENT_YEAR, CURRENT_YEAR + 1];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Reports</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Generate and export attendance and leave reports.</p>
      </div>

      {/* Report type tabs */}
      <div className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
        {(["attendance-summary", "leave-summary", "monthly-detail"] as ReportType[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => { setReportType(t); setRows([]); setGenerated(false); }}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              reportType === t
                ? "bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-100"
                : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            }`}
          >
            {t === "attendance-summary" && "Attendance Summary"}
            {t === "leave-summary" && "Leave Summary"}
            {t === "monthly-detail" && "Monthly Detail"}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="flex flex-wrap items-end gap-4">
          {reportType === "attendance-summary" && (
            <>
              <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
                Start date
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                />
              </label>
              <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
                End date
                <input
                  type="date"
                  value={endDate}
                  min={startDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                />
              </label>
            </>
          )}

          {(reportType === "leave-summary" || reportType === "monthly-detail") && (
            <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
              Year
              <select
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              >
                {years.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </label>
          )}

          {reportType === "monthly-detail" && (
            <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
              Month
              <select
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              >
                {months.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
              </select>
            </label>
          )}

          {isManager && staff.length > 0 && (
            <label className="flex flex-col gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
              Staff member
              <select
                value={staffFilter}
                onChange={(e) => setStaffFilter(e.target.value)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">All staff</option>
                {staff.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </label>
          )}

          <div className="flex gap-2 self-end">
            <button
              type="button"
              disabled={loading}
              onClick={handleGenerate}
              className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-60 dark:bg-teal-600 dark:hover:bg-teal-700"
            >
              {loading ? "Generating…" : "Generate"}
            </button>
            {generated && rows.length > 0 && (
              <button
                type="button"
                disabled={downloading}
                onClick={handleDownload}
                className="rounded-lg border border-teal-700 px-4 py-2 text-sm font-semibold text-teal-700 hover:bg-teal-50 disabled:opacity-60 dark:border-teal-500 dark:text-teal-400 dark:hover:bg-teal-950"
              >
                {downloading ? "…" : "Download Excel"}
              </button>
            )}
          </div>
        </div>

        {errorMessage && <p className="mt-3 text-sm text-rose-600 dark:text-rose-400">{errorMessage}</p>}
      </div>

      {/* Results table */}
      {generated && (
        rows.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No data found for the selected filters.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  {columns.map((col) => (
                    <th key={col.key} className="px-4 py-3 text-left font-medium text-slate-600 whitespace-nowrap dark:text-slate-400">
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {rows.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                    {columns.map((col) => (
                      <td key={col.key} className="px-4 py-3 text-slate-700 whitespace-nowrap dark:text-slate-300">
                        {fmtCell(row[col.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="border-t border-slate-100 px-4 py-2 text-xs text-slate-400 dark:border-slate-800 dark:text-slate-500">
              {rows.length} {rows.length === 1 ? "row" : "rows"}
            </div>
          </div>
        )
      )}
    </div>
  );
}
