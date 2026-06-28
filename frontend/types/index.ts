export type UserRole = "OWNER" | "ADMIN" | "MANAGER" | "STAFF";

export type ClinicStatus = "ACTIVE" | "SUSPENDED";

export type ClinicSummary = {
  id: string;
  name: string;
  slug: string;
  status: ClinicStatus;
  timezone: string;
};

export type Clinic = {
  id: string;
  name: string;
  slug: string;
  status: ClinicStatus;
  timezone: string;
  address: string | null;
  created_at: string;
  updated_at: string;
};

export type AuthUser = User & {
  clinic: ClinicSummary;
};

export type ClinicUpdateInput = {
  name?: string;
  timezone?: string;
  address?: string | null;
};

export type ClinicPublicInfo = {
  name: string;
  slug: string;
};

export type ClinicCreateInput = {
  name: string;
  slug: string;
  timezone: string;
  address?: string | null;
  owner_name: string;
  owner_email: string;
  owner_password: string;
};

export type PlatformClinic = {
  id: string;
  name: string;
  slug: string;
  status: ClinicStatus;
  timezone: string;
  address: string | null;
  user_count: number;
  created_at: string;
  updated_at: string;
};

export type PlatformClinicUpdateInput = {
  name?: string;
  timezone?: string;
  address?: string | null;
  owner_name?: string;
  owner_email?: string;
  owner_password?: string;
};

export type PlatformMetrics = {
  total_clinics: number;
  active_clinics: number;
  suspended_clinics: number;
  total_users: number;
};

export type EmploymentType =
  | "FULL_TIME"
  | "PART_TIME"
  | "CONTRACT"
  | "TEMPORARY";

export type UserStatus = "ACTIVE" | "INACTIVE" | "TERMINATED";

export type User = {
  id: string;
  clinic_id: string;
  name: string;
  email: string;
  phone: string | null;
  role: UserRole;
  employment_type: EmploymentType;
  hire_date: string | null;
  termination_date: string | null;
  status: UserStatus;
  created_at: string;
  updated_at: string;
};

export type StaffCreateInput = {
  name: string;
  email: string;
  phone?: string | null;
  password: string;
  role: UserRole;
  employment_type: EmploymentType;
  hire_date?: string | null;
};

export type StaffUpdateInput = {
  name?: string;
  email?: string;
  phone?: string | null;
  role?: UserRole;
  employment_type?: EmploymentType;
  hire_date?: string | null;
  termination_date?: string | null;
  status?: UserStatus;
};

export type Shift = {
  id: string;
  clinic_id: string;
  name: string;
  start_time: string;
  end_time: string;
  break_minutes: number;
  crosses_midnight: boolean;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type ShiftCreateInput = {
  name: string;
  start_time: string;
  end_time: string;
  break_minutes?: number;
  crosses_midnight?: boolean;
};

export type ScheduleStatus = "SCHEDULED" | "OFF" | "HOLIDAY" | "CANCELLED";

export type StaffSchedule = {
  id: string;
  clinic_id: string;
  user_id: string;
  shift_id: string | null;
  work_date: string;
  scheduled_start: string | null;
  scheduled_end: string | null;
  scheduled_break_minutes: number;
  status: ScheduleStatus;
  created_at: string;
  updated_at: string;
};

export type PunchType = "CLOCK_IN" | "CLOCK_OUT" | "BREAK_START" | "BREAK_END" | "MANUAL";
export type PunchSource = "WEB" | "MOBILE_WEB" | "ADMIN" | "QR" | "GPS" | "BIOMETRIC";

export type AttendancePunch = {
  id: string;
  clinic_id: string;
  user_id: string;
  punch_type: PunchType;
  punched_at: string;
  source: PunchSource;
  ip_address: string | null;
  created_at: string;
};

export type TodayStatus = {
  work_date: string;
  is_clocked_in: boolean;
  punches: AttendancePunch[];
  schedule: StaffSchedule | null;
  last_punch: AttendancePunch | null;
};

export type UserDayPunches = {
  user_id: string;
  user_name: string;
  punches: AttendancePunch[];
  is_clocked_in: boolean;
};

export type LeaveStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export type LeaveType = {
  id: string;
  clinic_id: string;
  name: string;
  default_days_per_year: number | null;
  requires_approval: boolean;
  tenure_based: boolean;
  allow_carryover: boolean;
  carryover_max_days: number | null;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type LeaveTypeCreateInput = {
  name: string;
  default_days_per_year?: number | null;
  requires_approval?: boolean;
  tenure_based?: boolean;
  allow_carryover?: boolean;
  carryover_max_days?: number | null;
};

export type LeaveTypeUpdateInput = {
  name?: string;
  default_days_per_year?: number | null;
  requires_approval?: boolean;
  tenure_based?: boolean;
  allow_carryover?: boolean;
  carryover_max_days?: number | null;
  active?: boolean;
};

export type LeaveRequest = {
  id: string;
  clinic_id: string;
  user_id: string;
  leave_type_id: string;
  reviewer_id: string | null;
  start_date: string;
  end_date: string;
  total_days: number;
  reason: string | null;
  status: LeaveStatus;
  reviewer_note: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  exceeds_per_request_max?: boolean;
  max_days_per_request?: number | null;
  policy_warning?: string | null;
};

export type LeaveRequestCreateInput = {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason?: string | null;
};

export type LeaveBalance = {
  id: string;
  clinic_id: string;
  user_id: string;
  leave_type_id: string;
  year: number;
  balance_days: number;
  carryover_days: number;
  used_days: number;
  remaining_days: number;
  created_at: string;
  updated_at: string;
};

export type AdjustBalanceInput = {
  user_id: string;
  leave_type_id: string;
  year: number;
  delta_days: number;
  reason: string;
};

export type LeaveBalanceAdjustment = {
  id: string;
  leave_balance_id: string;
  adjusted_by: string;
  delta_days: number;
  reason: string;
  created_at: string;
};

export type CorrectionStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export type AttendanceCorrectionRequest = {
  id: string;
  clinic_id: string;
  user_id: string;
  reviewer_id: string | null;
  work_date: string;
  status: CorrectionStatus;
  corrected_clock_in: string | null;
  corrected_clock_out: string | null;
  reason: string;
  reviewer_note: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CorrectionCreateInput = {
  work_date: string;
  corrected_clock_in?: string | null;
  corrected_clock_out?: string | null;
  reason: string;
};

export type AttendanceDayStatus =
  | "NOT_STARTED"
  | "WORKING"
  | "COMPLETED"
  | "ABSENT"
  | "HOLIDAY"
  | "ON_LEAVE";

export type AttendanceDay = {
  id: string;
  clinic_id: string;
  user_id: string;
  work_date: string;
  status: AttendanceDayStatus;
  scheduled_minutes: number | null;
  actual_clock_in: string | null;
  actual_clock_out: string | null;
  worked_minutes: number;
  regular_minutes: number;
  overtime_minutes: number;
  late_minutes: number;
  early_leave_minutes: number;
  break_minutes: number;
  is_locked: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ScheduleGenerateInput = {
  user_id: string;
  shift_id: string;
  start_date: string;
  end_date: string;
  weekdays: number[];
};

export type MonthlyClosing = {
  id: string;
  clinic_id: string;
  year: number;
  month: number;
  is_locked: boolean;
  locked_by: string | null;
  locked_at: string | null;
  unlocked_by: string | null;
  unlocked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  clinic_id: string;
  actor_id: string;
  actor_name: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
};

export type NavItem = {
  href: string;
  label: string;
  roles?: UserRole[];
};
