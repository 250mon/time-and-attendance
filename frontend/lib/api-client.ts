import axios from "axios";

import type {
  AdjustBalanceInput,
  AuditLog,
  LeaveBalanceAdjustment,
  AttendanceCorrectionRequest,
  AttendanceDay,
  AttendancePunch,
  AuthUser,
  Clinic,
  ClinicCreateInput,
  ClinicPublicInfo,
  ClinicUpdateInput,
  CorrectionCreateInput,
  PlatformClinic,
  PlatformClinicUpdateInput,
  PlatformMetrics,
  LeaveBalance,
  LeaveRequest,
  MonthlyClosing,
  LeaveRequestCreateInput,
  LeaveType,
  LeaveTypeCreateInput,
  LeaveTypeUpdateInput,
  ScheduleGenerateInput,
  Shift,
  ShiftCreateInput,
  StaffCreateInput,
  StaffSchedule,
  StaffUpdateInput,
  TodayStatus,
  User,
  UserDayPunches,
} from "@/types";

const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: backendUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Redirect to /login on 401, except for paths that manage their own auth state.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? "";
    const selfManaged = url.includes("/auth/me") || url.includes("/platform/");
    if (axios.isAxiosError(error) && error.response?.status === 401 && !selfManaged) {
      window.location.replace("/login");
    }
    return Promise.reject(error);
  },
);

export async function fetchHealth(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>("/health");
  return response.data;
}

export async function loginRequest(
  email: string,
  password: string,
  clinicSlug?: string,
): Promise<AuthUser> {
  const response = await apiClient.post<AuthUser>("/auth/login", {
    email,
    password,
    clinic_slug: clinicSlug || null,
  });
  return response.data;
}

export async function logoutRequest(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUser>("/auth/me");
  return response.data;
}

export async function fetchClinicBySlug(slug: string): Promise<ClinicPublicInfo> {
  const response = await apiClient.get<ClinicPublicInfo>(`/clinics/by-slug/${slug}`);
  return response.data;
}

export async function fetchStaff(): Promise<User[]> {
  const response = await apiClient.get<User[]>("/staff");
  return response.data;
}

export async function fetchStaffMember(userId: string): Promise<User> {
  const response = await apiClient.get<User>(`/staff/${userId}`);
  return response.data;
}

export async function createStaffMember(payload: StaffCreateInput): Promise<User> {
  const response = await apiClient.post<User>("/staff", payload);
  return response.data;
}

export async function updateStaffMember(
  userId: string,
  payload: StaffUpdateInput,
): Promise<User> {
  const response = await apiClient.patch<User>(`/staff/${userId}`, payload);
  return response.data;
}

export async function deactivateStaffMember(userId: string): Promise<User> {
  const response = await apiClient.delete<User>(`/staff/${userId}`);
  return response.data;
}

export async function fetchShifts(): Promise<Shift[]> {
  const response = await apiClient.get<Shift[]>("/shifts");
  return response.data;
}

export async function createShift(payload: ShiftCreateInput): Promise<Shift> {
  const response = await apiClient.post<Shift>("/shifts", payload);
  return response.data;
}

export async function updateShift(shiftId: string, payload: Partial<ShiftCreateInput & { active: boolean }>): Promise<Shift> {
  const response = await apiClient.patch<Shift>(`/shifts/${shiftId}`, payload);
  return response.data;
}

export async function deactivateShift(shiftId: string): Promise<Shift> {
  const response = await apiClient.delete<Shift>(`/shifts/${shiftId}`);
  return response.data;
}

export async function fetchSchedules(params?: {
  start_date?: string;
  end_date?: string;
  user_id?: string;
}): Promise<StaffSchedule[]> {
  const response = await apiClient.get<StaffSchedule[]>("/schedules", { params });
  return response.data;
}

export async function generateSchedules(payload: ScheduleGenerateInput): Promise<StaffSchedule[]> {
  const response = await apiClient.post<StaffSchedule[]>("/schedules/generate", payload);
  return response.data;
}

export async function deleteSchedule(scheduleId: string): Promise<void> {
  await apiClient.delete(`/schedules/${scheduleId}`);
}

export async function clockIn(): Promise<AttendancePunch> {
  const response = await apiClient.post<AttendancePunch>("/attendance/clock-in");
  return response.data;
}

export async function clockOut(): Promise<AttendancePunch> {
  const response = await apiClient.post<AttendancePunch>("/attendance/clock-out");
  return response.data;
}

export async function fetchTodayStatus(): Promise<TodayStatus> {
  const response = await apiClient.get<TodayStatus>("/attendance/today");
  return response.data;
}

export async function fetchMyPunches(days = 30): Promise<AttendancePunch[]> {
  const response = await apiClient.get<AttendancePunch[]>("/attendance/me", { params: { days } });
  return response.data;
}

export async function fetchDailyAttendance(date?: string): Promise<UserDayPunches[]> {
  const response = await apiClient.get<UserDayPunches[]>("/attendance/daily", {
    params: date ? { date } : undefined,
  });
  return response.data;
}

// ── Leave Types ──────────────────────────────────────────────────────────────

export async function fetchLeaveTypes(includeInactive = false): Promise<LeaveType[]> {
  const response = await apiClient.get<LeaveType[]>("/leave/types", {
    params: includeInactive ? { include_inactive: true } : undefined,
  });
  return response.data;
}

export async function createLeaveType(payload: LeaveTypeCreateInput): Promise<LeaveType> {
  const response = await apiClient.post<LeaveType>("/leave/types", payload);
  return response.data;
}

export async function updateLeaveType(id: string, payload: LeaveTypeUpdateInput): Promise<LeaveType> {
  const response = await apiClient.patch<LeaveType>(`/leave/types/${id}`, payload);
  return response.data;
}

export async function deactivateLeaveType(id: string): Promise<LeaveType> {
  const response = await apiClient.delete<LeaveType>(`/leave/types/${id}`);
  return response.data;
}

// ── Leave Requests ────────────────────────────────────────────────────────────

export async function fetchLeaveRequests(params?: {
  status?: string;
  user_id?: string;
}): Promise<LeaveRequest[]> {
  const response = await apiClient.get<LeaveRequest[]>("/leave/requests", { params });
  return response.data;
}

export async function createLeaveRequest(payload: LeaveRequestCreateInput): Promise<LeaveRequest> {
  const response = await apiClient.post<LeaveRequest>("/leave/requests", payload);
  return response.data;
}

export async function approveLeaveRequest(id: string, reviewerNote?: string): Promise<LeaveRequest> {
  const response = await apiClient.post<LeaveRequest>(
    `/leave/requests/${id}/approve`,
    { reviewer_note: reviewerNote ?? null },
  );
  return response.data;
}

export async function rejectLeaveRequest(id: string, reviewerNote?: string): Promise<LeaveRequest> {
  const response = await apiClient.post<LeaveRequest>(
    `/leave/requests/${id}/reject`,
    { reviewer_note: reviewerNote ?? null },
  );
  return response.data;
}

export async function cancelLeaveRequest(id: string): Promise<LeaveRequest> {
  const response = await apiClient.delete<LeaveRequest>(`/leave/requests/${id}`);
  return response.data;
}

export async function fetchLeaveBalances(params?: {
  user_id?: string;
  year?: number;
}): Promise<LeaveBalance[]> {
  const response = await apiClient.get<LeaveBalance[]>("/leave/balances", { params });
  return response.data;
}

export async function adjustLeaveBalance(payload: AdjustBalanceInput): Promise<LeaveBalance> {
  const response = await apiClient.post<LeaveBalance>("/leave/balances/adjust", payload);
  return response.data;
}

export async function fetchLeaveAdjustments(balanceId: string): Promise<LeaveBalanceAdjustment[]> {
  const response = await apiClient.get<LeaveBalanceAdjustment[]>(`/leave/balances/${balanceId}/adjustments`);
  return response.data;
}

export async function fetchCorrections(params?: {
  status?: string;
  user_id?: string;
}): Promise<AttendanceCorrectionRequest[]> {
  const response = await apiClient.get<AttendanceCorrectionRequest[]>("/attendance/corrections", { params });
  return response.data;
}

export async function createCorrection(payload: CorrectionCreateInput): Promise<AttendanceCorrectionRequest> {
  const response = await apiClient.post<AttendanceCorrectionRequest>("/attendance/corrections", payload);
  return response.data;
}

export async function approveCorrection(id: string, reviewerNote?: string): Promise<AttendanceCorrectionRequest> {
  const response = await apiClient.post<AttendanceCorrectionRequest>(
    `/attendance/corrections/${id}/approve`,
    { reviewer_note: reviewerNote ?? null },
  );
  return response.data;
}

export async function rejectCorrection(id: string, reviewerNote?: string): Promise<AttendanceCorrectionRequest> {
  const response = await apiClient.post<AttendanceCorrectionRequest>(
    `/attendance/corrections/${id}/reject`,
    { reviewer_note: reviewerNote ?? null },
  );
  return response.data;
}

export async function cancelCorrection(id: string): Promise<AttendanceCorrectionRequest> {
  const response = await apiClient.delete<AttendanceCorrectionRequest>(`/attendance/corrections/${id}`);
  return response.data;
}

export async function fetchAttendanceDays(params?: {
  start_date?: string;
  end_date?: string;
  user_id?: string;
}): Promise<AttendanceDay[]> {
  const response = await apiClient.get<AttendanceDay[]>("/attendance/days", { params });
  return response.data;
}

// ── Clinic ────────────────────────────────────────────────────────────────────

export async function fetchClinic(): Promise<Clinic> {
  const response = await apiClient.get<Clinic>("/clinics/me");
  return response.data;
}

export async function updateClinic(data: ClinicUpdateInput): Promise<Clinic> {
  const response = await apiClient.patch<Clinic>("/clinics/me", data);
  return response.data;
}

// ── Closings ──────────────────────────────────────────────────────────────────

export async function fetchClosings(params?: { year?: number }): Promise<MonthlyClosing[]> {
  const response = await apiClient.get<MonthlyClosing[]>("/closings", { params });
  return response.data;
}

export async function lockMonth(year: number, month: number): Promise<MonthlyClosing> {
  const response = await apiClient.post<MonthlyClosing>(`/closings/${year}/${month}/lock`);
  return response.data;
}

export async function unlockMonth(year: number, month: number): Promise<MonthlyClosing> {
  const response = await apiClient.post<MonthlyClosing>(`/closings/${year}/${month}/unlock`);
  return response.data;
}

// ── Audit Logs ────────────────────────────────────────────────────────────────

export async function fetchAuditLogs(params?: {
  action?: string;
  limit?: number;
  offset?: number;
}): Promise<AuditLog[]> {
  const response = await apiClient.get<AuditLog[]>("/audit-logs", { params });
  return response.data;
}

// ── Reports ───────────────────────────────────────────────────────────────────

export async function fetchAttendanceSummary(params: {
  start_date: string;
  end_date: string;
  user_id?: string;
}): Promise<Record<string, unknown>[]> {
  const response = await apiClient.get<Record<string, unknown>[]>("/reports/attendance-summary", { params });
  return response.data;
}

export async function fetchLeaveSummaryReport(params: {
  year: number;
  user_id?: string;
}): Promise<Record<string, unknown>[]> {
  const response = await apiClient.get<Record<string, unknown>[]>("/reports/leave-summary", { params });
  return response.data;
}

export async function fetchMonthlyDetail(params: {
  year: number;
  month: number;
  user_id?: string;
}): Promise<Record<string, unknown>[]> {
  const response = await apiClient.get<Record<string, unknown>[]>("/reports/monthly-detail", { params });
  return response.data;
}

export async function downloadReport(
  endpoint: string,
  params: Record<string, unknown>,
): Promise<Blob> {
  const response = await apiClient.get<Blob>(endpoint, {
    params: { ...params, format: "xlsx" },
    responseType: "blob",
  });
  return response.data;
}

// ── Platform Admin ────────────────────────────────────────────────────────────

function platformHeaders(token: string) {
  return { "X-Platform-Token": token };
}

export async function createPlatformClinic(
  token: string,
  data: ClinicCreateInput,
): Promise<PlatformClinic> {
  const response = await apiClient.post<PlatformClinic>("/platform/clinics", data, {
    headers: platformHeaders(token),
  });
  return response.data;
}

export async function updatePlatformClinic(
  token: string,
  clinicId: string,
  data: PlatformClinicUpdateInput,
): Promise<PlatformClinic> {
  const response = await apiClient.patch<PlatformClinic>(`/platform/clinics/${clinicId}`, data, {
    headers: platformHeaders(token),
  });
  return response.data;
}

export async function fetchPlatformClinics(token: string): Promise<PlatformClinic[]> {
  const response = await apiClient.get<PlatformClinic[]>("/platform/clinics", {
    headers: platformHeaders(token),
  });
  return response.data;
}

export async function fetchPlatformMetrics(token: string): Promise<PlatformMetrics> {
  const response = await apiClient.get<PlatformMetrics>("/platform/metrics", {
    headers: platformHeaders(token),
  });
  return response.data;
}

export async function suspendPlatformClinic(
  token: string,
  clinicId: string,
): Promise<PlatformClinic> {
  const response = await apiClient.post<PlatformClinic>(
    `/platform/clinics/${clinicId}/suspend`,
    null,
    { headers: platformHeaders(token) },
  );
  return response.data;
}

export async function activatePlatformClinic(
  token: string,
  clinicId: string,
): Promise<PlatformClinic> {
  const response = await apiClient.post<PlatformClinic>(
    `/platform/clinics/${clinicId}/activate`,
    null,
    { headers: platformHeaders(token) },
  );
  return response.data;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return fallback;
}
