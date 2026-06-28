from enum import StrEnum


class ClinicStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class UserRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"


class EmploymentType(StrEnum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TERMINATED = "TERMINATED"


class ScheduleStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    OFF = "OFF"
    HOLIDAY = "HOLIDAY"
    CANCELLED = "CANCELLED"


class PunchType(StrEnum):
    CLOCK_IN = "CLOCK_IN"
    CLOCK_OUT = "CLOCK_OUT"
    BREAK_START = "BREAK_START"
    BREAK_END = "BREAK_END"
    MANUAL = "MANUAL"


class PunchSource(StrEnum):
    WEB = "WEB"
    MOBILE_WEB = "MOBILE_WEB"
    ADMIN = "ADMIN"
    QR = "QR"
    GPS = "GPS"
    BIOMETRIC = "BIOMETRIC"


class LeaveStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class CorrectionStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class AttendanceDayStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    WORKING = "WORKING"
    COMPLETED = "COMPLETED"
    ABSENT = "ABSENT"
    HOLIDAY = "HOLIDAY"
    ON_LEAVE = "ON_LEAVE"


class AuditAction(StrEnum):
    CORRECTION_APPROVED = "CORRECTION_APPROVED"
    CORRECTION_REJECTED = "CORRECTION_REJECTED"
    LEAVE_APPROVED = "LEAVE_APPROVED"
    LEAVE_REJECTED = "LEAVE_REJECTED"
    LEAVE_SUBMITTED = "LEAVE_SUBMITTED"
    BALANCE_ADJUSTED = "BALANCE_ADJUSTED"
    MONTH_LOCKED = "MONTH_LOCKED"
    MONTH_UNLOCKED = "MONTH_UNLOCKED"
    REPORT_EXPORTED = "REPORT_EXPORTED"
