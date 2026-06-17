Below is a first PRD for the **Time & Attendance + Leave Management Software for a Small Clinic**.

# Product Requirements Document

# Time & Attendance and Leave Management Software for a Small Clinic

## 1. Product Overview

### 1.1 Product Name

Working name: **ClinicTime**

### 1.2 Purpose

ClinicTime is a lightweight web-based time-and-attendance and leave-management system designed for small clinic operations. It allows clinic staff to clock in and out, view attendance records, request leave, and check leave balances. Clinic managers or owners can manage staff schedules, approve leave and attendance corrections, monitor daily staffing, and export monthly attendance data for payroll and administrative review.

### 1.3 Target Users

The primary target users are small outpatient clinics, private practices, and similar healthcare facilities with approximately 3 to 30 employees.

Typical users include:

- Clinic owner or director
- Office manager
- Head nurse
- Nurses
- Reception staff
- Physical therapists or assistants
- Part-time staff

### 1.4 Product Vision

To replace manual attendance books, spreadsheets, and informal leave tracking with a simple, auditable, mobile-friendly system that improves administrative accuracy, reduces payroll disputes, and helps maintain adequate staffing in daily clinic operations.

------

## 2. Problem Statement

Small clinics often track staff attendance and leave using paper logs, Excel files, messaging apps, or verbal approvals. These methods create several problems:

1. Clock-in and clock-out records are difficult to verify.
2. Missed punches and late corrections are handled inconsistently.
3. Leave balances are manually calculated and prone to error.
4. Monthly payroll preparation requires repetitive manual work.
5. It is difficult to see staffing shortages caused by leave approvals.
6. Attendance disputes are difficult to resolve because historical edits are not auditable.
7. Clinic owners lack a clear daily and monthly view of staff attendance.

ClinicTime should solve these problems with a focused, low-friction system suitable for small-clinic workflows.

------

## 3. Goals and Objectives

### 3.1 Business Goals

- Reduce manual attendance administration.
- Improve accuracy of payroll-related attendance data.
- Create transparent leave tracking.
- Reduce disputes regarding lateness, overtime, missed punches, and leave balances.
- Help clinic managers maintain minimum staffing levels.
- Provide exportable monthly reports.

### 3.2 Product Goals

- Allow staff to clock in and out within 5 seconds.
- Allow staff to request leave without messaging or paper forms.
- Allow managers to approve or reject leave and correction requests.
- Generate monthly attendance summaries.
- Preserve audit history for all manual changes.
- Support simple deployment for a single clinic.

### 3.3 Non-Goals for MVP

The MVP will not include:

- Full payroll calculation
- Salary payment processing
- Tax reporting
- Biometric device integration
- Complex multi-branch HR management
- AI-based shift optimization
- Native iOS or Android apps
- Full legal compliance automation

The system may provide data useful for payroll and compliance, but it will not be a legal or payroll advisory engine.

------

## 4. User Personas

### 4.1 Clinic Owner / Director

The clinic owner wants a reliable overview of staff attendance, leave usage, lateness, overtime, and monthly payroll-related records. The owner needs final control over settings, reports, and locked monthly records.

Key needs:

- View all staff attendance
- Export monthly reports
- Configure leave rules
- Lock monthly records
- Review audit logs

### 4.2 Manager / Head Nurse

The manager handles daily operations, staff scheduling, leave approvals, and attendance corrections.

Key needs:

- See who is currently present
- Check late or absent staff
- Approve leave requests
- Approve missed-punch corrections
- Manage shift schedules
- Avoid approving leave that causes understaffing

### 4.3 Staff Member

The staff member uses the system to clock in, clock out, request leave, check leave balance, and submit corrections when a punch was missed.

Key needs:

- Clock in/out quickly
- View today’s schedule
- Request leave
- See remaining leave balance
- Submit correction requests
- View personal attendance history

------

## 5. Scope

### 5.1 MVP Scope

The MVP includes:

1. Authentication and role-based access
2. Staff management
3. Shift and schedule management
4. Clock-in and clock-out
5. Attendance calculation
6. Missed-punch correction requests
7. Leave request and approval
8. Leave balance tracking
9. Monthly attendance report
10. Payroll export
11. Audit log
12. Basic clinic settings

### 5.2 Post-MVP Scope

Future versions may include:

1. GPS-based clock-in
2. QR-code clock-in
3. Clinic Wi-Fi or IP restriction
4. KakaoTalk/SMS/email notifications
5. Public holiday calendar integration
6. Overtime approval workflow
7. Biometric device integration
8. Multi-branch support
9. Payroll vendor integration
10. Native mobile app
11. Advanced labor-rule engine

------

## 6. Functional Requirements

## 6.1 Authentication and Authorization

### Description

Users must log in securely and receive access based on their role.

### Requirements

- The system shall allow users to log in with email and password.
- The system shall support the following roles:
  - Owner/Admin
  - Manager
  - Staff
- The system shall restrict access based on role.
- The system shall allow admins to create, deactivate, and edit staff accounts.
- The system shall allow users to change their password.
- The system shall automatically log users out after a configurable inactivity period.

### Acceptance Criteria

- Staff cannot access other staff members’ private attendance records.
- Managers can view and manage assigned staff attendance.
- Admins can view and manage all data.
- Deactivated users cannot log in.

------

## 6.2 Staff Management

### Description

Admins and managers need to manage staff profiles and employment information.

### Requirements

The system shall support staff profiles with:

- Name
- Email
- Phone number
- Role
- Employment type
- Hire date
- Termination date
- Active/inactive status
- Default shift
- Leave policy assignment

Employment types should include:

- Full-time
- Part-time
- Contract
- Temporary

### Acceptance Criteria

- Admin can create a new staff member.
- Admin can deactivate a staff member without deleting historical records.
- Admin can assign role and employment type.
- Historical attendance records remain available after staff deactivation.

------

## 6.3 Shift and Schedule Management

### Description

The clinic must be able to define work shifts and assign schedules to staff.

### Requirements

The system shall allow managers/admins to:

- Create shift templates
- Assign shifts to individual staff
- Edit schedules by day
- View schedules in calendar format
- Support shifts that cross midnight
- Configure break duration
- Mark days as off-duty

A shift shall include:

- Shift name
- Start time
- End time
- Break duration
- Workday type
- Whether the shift crosses midnight

### Acceptance Criteria

- Manager can assign a staff member to a shift on a specific date.
- Staff can see their assigned schedule.
- The system can distinguish scheduled workdays from off-days.
- The system can handle a night shift crossing midnight.

------

## 6.4 Clock-In and Clock-Out

### Description

Staff must be able to record attendance easily.

### Requirements

The system shall allow staff to:

- Clock in
- Clock out
- View current attendance status
- View today’s scheduled shift
- See whether clock-in was late
- See whether clock-out was early or complete

Each punch record shall store:

- Staff ID
- Punch type
- Timestamp
- IP address
- Device information
- Source method
- Creation timestamp

Initial source methods:

- Web
- Mobile web
- Admin manual entry

Future source methods:

- QR code
- GPS
- Biometric device
- Clinic Wi-Fi/IP validation

### Acceptance Criteria

- Staff can clock in only once per active work session.
- Staff can clock out after clocking in.
- Staff cannot directly edit raw punch records.
- Raw punch records are preserved even after correction.

------

## 6.5 Attendance Calculation

### Description

The system must calculate daily attendance summaries from schedules, punches, and approved corrections.

### Requirements

The system shall calculate:

- Actual start time
- Actual end time
- Total worked minutes
- Break minutes
- Regular work minutes
- Overtime minutes
- Late minutes
- Early-leave minutes
- Night work minutes
- Holiday work minutes
- Attendance status

Attendance statuses shall include:

- Not started
- Working
- Completed
- Late
- Early leave
- Absent
- Leave
- Missing punch
- Manually corrected
- Locked

### Acceptance Criteria

- If staff clocks in after scheduled start time, late minutes are calculated.
- If staff clocks out before scheduled end time, early-leave minutes are calculated.
- If staff does not clock out, the day is marked as missing punch.
- If approved leave covers the full day, the day is marked as leave.
- Attendance summaries can be recalculated from raw punches and correction records.

------

## 6.6 Missed-Punch and Attendance Correction

### Description

Staff may forget to clock in or clock out. Corrections should be request-based and auditable.

### Requirements

The system shall allow staff to submit correction requests with:

- Work date
- Requested clock-in time
- Requested clock-out time
- Reason
- Optional attachment or note

The system shall allow managers/admins to:

- Approve correction requests
- Reject correction requests
- Add rejection reason
- View correction history

### Acceptance Criteria

- Staff cannot directly change attendance records.
- Approved corrections update calculated attendance summaries.
- Original raw punch records remain unchanged.
- All approvals and rejections are logged.

------

## 6.7 Leave Management

### Description

Staff should request leave through the system, and managers should approve or reject requests.

### Requirements

The system shall support leave types including:

- Annual leave
- Half-day annual leave
- Hourly leave
- Sick leave
- Unpaid leave
- Special leave

Each leave type shall have configurable properties:

- Paid or unpaid
- Deducts annual leave balance or not
- Unit: day, half-day, hour
- Requires approval
- Active/inactive

Staff shall be able to:

- Submit leave request
- Select leave type
- Select date or time range
- Enter reason
- View approval status
- Cancel pending request
- View leave history

Managers/admins shall be able to:

- Approve leave
- Reject leave
- Add rejection reason
- View team leave calendar
- View leave balance before approval

Admins shall be able to:

- Enter historical leave records for existing employees during initial setup
- Import historical leave records in batch using a CSV file

### Acceptance Criteria

- Staff cannot request annual leave exceeding available balance unless admin override is enabled.
- Approved annual leave deducts from leave balance.
- Rejected leave does not deduct balance.
- Pending leave is visible to manager.
- Approved leave appears on the staff schedule and attendance calendar.
- Admin can manually add past approved leave for an existing employee.
- Admin can upload a CSV file of historical leave records and preview validation errors before import.
- Imported historical leave updates leave history and balances without requiring manager approval.

------

## 6.8 Leave Balance

### Description

The system must track each staff member’s leave balance.

### Requirements

The system shall maintain annual leave balances by year.

Leave balance shall include:

- Accrued days
- Used days
- Pending days
- Adjusted days
- Remaining days

Admins shall be able to:

- Manually adjust leave balance
- Enter adjustment reason
- View adjustment history
- Set opening leave balances for existing employees during onboarding
- Recalculate balances from imported historical leave records

### Acceptance Criteria

- Staff can view remaining annual leave.
- Manager can view leave balance during approval.
- Manual adjustments require a reason.
- Leave balance changes are auditable.
- Opening balances and historical imports are auditable.
- Imported leave records are distinguishable from normal staff-submitted leave requests.

------

## 6.9 Minimum Staffing Warning

### Description

Small clinics must avoid approving leave that results in insufficient staffing.

### Requirements

The system shall allow admins to configure minimum staffing rules, such as:

- Minimum number of nurses per day
- Minimum number of reception staff per day
- Minimum total staff per day

When a manager approves leave, the system shall warn if approval would violate a staffing rule.

### Acceptance Criteria

- Manager receives a warning before approving leave that creates a staffing shortage.
- Manager can still approve with override permission.
- Override approval requires a reason.
- Warning and override are logged.

------

## 6.10 Reports and Exports

### Description

The system must generate monthly reports for payroll and administrative review.

### Requirements

The system shall provide:

- Daily attendance report
- Monthly staff attendance summary
- Leave usage report
- Late/early-leave report
- Overtime report
- Missing-punch report
- Payroll export

Reports shall be exportable as:

- Excel
- CSV

Payroll export shall include:

- Staff name
- Month
- Scheduled workdays
- Actual worked days
- Regular hours
- Overtime hours
- Night work hours
- Holiday work hours
- Late count
- Early-leave count
- Annual leave used
- Unpaid leave
- Missing punches
- Manual corrections

### Acceptance Criteria

- Admin can export monthly attendance report.
- Exported data matches on-screen data.
- Locked months cannot be modified without admin unlock.
- Reports can be filtered by staff, date, role, and employment type.

------

## 6.11 Monthly Closing and Locking

### Description

Once monthly attendance is reviewed, the records should be locked to prevent unauthorized retroactive changes.

### Requirements

The system shall allow admins to:

- Review monthly attendance
- Identify unresolved issues
- Lock a month
- Unlock a month with reason

Before locking, the system shall warn about:

- Missing punches
- Pending correction requests
- Pending leave requests
- Unapproved overtime, if applicable

### Acceptance Criteria

- Locked attendance records cannot be edited by staff or managers.
- Admin can unlock a month only with reason.
- Lock and unlock actions are recorded in the audit log.

------

## 6.12 Audit Log

### Description

The system must preserve a reliable history of important changes.

### Requirements

The system shall log:

- User creation and deactivation
- Role changes
- Shift changes
- Schedule changes
- Punch corrections
- Leave approvals and rejections
- Historical leave entry and import
- Leave balance adjustments
- Opening leave balance setup
- Monthly locking and unlocking
- Report generation
- Admin overrides

Audit log entries shall include:

- Actor
- Action
- Entity type
- Entity ID
- Previous value
- New value
- Reason, if applicable
- Timestamp

### Acceptance Criteria

- Admin can view audit logs.
- Audit logs cannot be edited through the application.
- Important manual changes require reason entry.

------

# 7. Non-Functional Requirements

## 7.1 Usability

- Clock-in/out should require no more than two taps after login.
- UI must be mobile-friendly.
- Staff-facing screens should be simple and readable.
- Manager dashboard should highlight exceptions first:
  - Late
  - Absent
  - Missing punch
  - Pending leave
  - Pending corrections

## 7.2 Performance

- Dashboard should load within 2 seconds under normal clinic usage.
- Clock-in/out should complete within 1 second after submission.
- Monthly report generation should complete within 10 seconds for up to 100 staff.

## 7.3 Availability

- Target availability: 99% for clinic operating hours.
- System should support local or cloud deployment.
- Backups should run at least daily.

## 7.4 Security

- Passwords must be hashed using a strong password hashing algorithm.
- HTTPS must be used in production.
- Role-based authorization must be enforced server-side.
- Sensitive actions must be audited.
- Admin access should support two-factor authentication in a later version.
- Raw attendance records should not be physically deleted by ordinary users.

## 7.5 Privacy

- The system should collect only necessary attendance data.
- GPS location should be optional and disabled by default in MVP.
- Staff should be informed if location, IP, or device information is collected.
- Access to staff attendance data should be limited by role.

## 7.6 Maintainability

- Business rules should be configurable.
- Attendance calculation logic should be separated from UI code.
- Raw punch data and calculated attendance summaries should be stored separately.
- Leave accrual logic should be modular.
- Database migrations should be version-controlled.

------

# 8. Data Requirements

## 8.1 Core Entities

Required entities:

- Clinic
- User
- Role
- Shift
- Staff Schedule
- Attendance Punch
- Attendance Day
- Attendance Correction Request
- Leave Type
- Leave Request
- Leave Balance
- Leave Import Batch
- Holiday
- Monthly Closing
- Audit Log

## 8.2 Data Retention

Recommended default retention:

- Raw attendance records: minimum 3 years
- Leave records: minimum 3 years
- Audit logs: minimum 3 years
- Exported reports: configurable

Actual retention should be configurable according to clinic policy and applicable law.

------

# 9. MVP User Stories

## Staff User Stories

### Clock In

As a staff member, I want to clock in when I arrive at the clinic so that my attendance is recorded accurately.

Acceptance criteria:

- I can see today’s shift.
- I can tap Clock In.
- I can see successful clock-in confirmation.
- I cannot clock in twice for the same active session.

### Clock Out

As a staff member, I want to clock out when I leave the clinic so that my workday is completed.

Acceptance criteria:

- I can tap Clock Out after clocking in.
- I can see total worked time.
- If I forget to clock out, the system marks the day as missing punch.

### Request Leave

As a staff member, I want to request annual leave from my phone so that I do not need to submit a paper form.

Acceptance criteria:

- I can select leave type and date.
- I can see my remaining leave balance.
- I can submit a reason.
- I can view approval status.

### Request Attendance Correction

As a staff member, I want to request correction for a missed punch so that my attendance record can be fixed with approval.

Acceptance criteria:

- I can select the date.
- I can enter requested time.
- I can provide a reason.
- I can see approval or rejection result.

------

## Manager User Stories

### View Daily Attendance

As a manager, I want to see who is present, late, absent, or missing a punch so that I can manage clinic operations.

Acceptance criteria:

- I can see today’s staff list.
- Late and absent staff are highlighted.
- Missing punches are highlighted.
- I can filter by role or employment type.

### Approve Leave

As a manager, I want to approve or reject leave requests so that staff absences are properly managed.

Acceptance criteria:

- I can view pending leave requests.
- I can see leave balance.
- I can see staffing warnings.
- I can approve or reject with a comment.

### Approve Correction

As a manager, I want to approve missed-punch corrections so that attendance records remain accurate and auditable.

Acceptance criteria:

- I can see original punch data.
- I can see requested correction.
- I can approve or reject.
- The action is logged.

------

## Admin User Stories

### Configure Leave Policy

As an admin, I want to configure leave types and leave balances so that the system reflects clinic policy.

Acceptance criteria:

- I can create leave types.
- I can set whether leave is paid.
- I can set whether leave deducts annual leave.
- I can manually adjust leave balance with reason.

### Import Historical Leave

As an admin, I want to enter or import existing employees' past leave records so that leave balances are accurate when the clinic starts using the system.

Acceptance criteria:

- I can add an individual historical leave record manually.
- I can import historical leave records from CSV.
- I can preview invalid rows before committing an import.
- Imported records update leave history and balances.
- Import actions are audited.

### Export Monthly Report

As an admin, I want to export monthly attendance data so that I can prepare payroll.

Acceptance criteria:

- I can select month and staff.
- I can export Excel or CSV.
- Export includes attendance and leave data.
- Exported values match the system dashboard.

### Lock Month

As an admin, I want to lock a month after review so that records cannot be changed casually after payroll processing.

Acceptance criteria:

- I can see unresolved issues before locking.
- I can lock the month.
- Locked records cannot be modified without unlock.
- Unlock requires reason and is audited.

------

# 10. Business Rules

## 10.1 Attendance Rules

- A staff member may have only one active work session at a time.
- Clock-in after scheduled start time creates late minutes.
- Clock-out before scheduled end time creates early-leave minutes.
- Missing clock-in or clock-out creates missing-punch status.
- Approved full-day leave overrides absence status.
- Approved partial leave modifies expected working time.
- Raw punches are immutable.
- Corrections are stored separately and require approval.

## 10.2 Leave Rules

- Annual leave deducts from leave balance after approval.
- Rejected leave does not deduct leave balance.
- Pending leave may be shown separately from used leave.
- Leave cancellation after approval requires manager or admin approval.
- Leave balance adjustments require reason.
- Leave cannot normally be requested for a locked month unless admin override is enabled.

## 10.3 Monthly Closing Rules

- Month can be locked only by admin.
- Locked records cannot be changed by staff or manager.
- Unlocking requires reason.
- All lock/unlock events are audited.

------

# 11. UX Requirements

## 11.1 Staff Home Screen

Must show:

- Today’s date
- Scheduled shift
- Current attendance status
- Clock In / Clock Out button
- Leave balance shortcut
- Correction request shortcut

## 11.2 Manager Dashboard

Must show:

- Present staff
- Absent staff
- Late staff
- Staff on leave
- Missing-punch records
- Pending leave requests
- Pending correction requests

## 11.3 Leave Request Screen

Must show:

- Leave type
- Date/time selector
- Remaining balance
- Reason field
- Submit button
- Existing approved leave calendar, optional

## 11.4 Monthly Report Screen

Must show:

- Month selector
- Staff filter
- Attendance summary table
- Exception list
- Export button
- Lock month button

------

# 12. System Architecture Requirements

Recommended MVP architecture:

- Frontend: Next.js + React + TypeScript
- Backend: FastAPI or Next.js API layer
- Database: PostgreSQL
- Authentication: session-based or JWT-based authentication
- Deployment: Docker Compose
- Export generation: server-side Excel/CSV generation
- Background jobs: scheduled daily recalculation and monthly accrual update

The system should separate:

- Raw punch capture
- Attendance calculation
- Leave balance calculation
- Approval workflow
- Reporting

------

# 13. Key Metrics

## Product Usage Metrics

- Daily active staff users
- Clock-in completion rate
- Clock-out completion rate
- Number of missed-punch requests
- Number of leave requests
- Average approval time
- Monthly report export count

## Operational Metrics

- Late arrivals per month
- Missing-punch rate
- Leave balance discrepancy count
- Payroll correction count
- Number of manual attendance edits

## Success Metrics

The MVP is successful if:

- More than 90% of workdays have complete clock-in/out records.
- Monthly attendance report preparation time is reduced by at least 50%.
- Leave balance can be calculated without manual Excel reconciliation.
- Managers can identify daily attendance exceptions within 1 minute.
- Attendance correction history is fully auditable.

------

# 14. Risks and Mitigations

## Risk 1: Staff Forget to Clock Out

Mitigation:

- Show dashboard warning.
- Send reminder notification in later version.
- Provide correction request workflow.

## Risk 2: Staff Dispute Attendance Records

Mitigation:

- Preserve immutable raw punch data.
- Use approval-based corrections.
- Maintain audit log.

## Risk 3: Leave Rules Become Legally Complex

Mitigation:

- Keep policy configurable.
- Avoid hard-coded legal assumptions.
- Allow manual adjustment with audit trail.

## Risk 4: Small Clinic Does Not Want Complex Software

Mitigation:

- Keep staff UI extremely simple.
- Hide advanced settings from regular users.
- Prioritize mobile-first clock-in/out.

## Risk 5: Unauthorized Data Access

Mitigation:

- Enforce role-based access server-side.
- Use secure authentication.
- Log admin actions.
- Limit staff visibility to their own records.

------

# 15. MVP Release Criteria

The MVP can be released when the following are complete:

1. Staff can log in.
2. Admin can create staff accounts.
3. Staff can clock in and clock out.
4. Attendance records are calculated correctly.
5. Staff can request leave.
6. Manager can approve or reject leave.
7. Leave balance is updated.
8. Staff can request attendance correction.
9. Manager can approve or reject corrections.
10. Admin can export monthly attendance report.
11. Audit logs are generated for key actions.
12. Basic role-based access control is enforced.
13. System is deployed with database backup.

------

# 16. Open Questions

1. Should the first version support only one clinic or multiple clinic branches?
2. Should part-time staff have different leave accrual rules?
3. Should hourly leave be included in MVP or delayed?
4. Should clock-in be allowed only from clinic Wi-Fi or allowed remotely?
5. Should the system integrate with payroll software?
6. Should public holidays be manually entered or automatically imported?
7. Should managers be able to approve their own leave?
8. Should overtime require pre-approval?
9. Should staff receive notifications by email, SMS, or KakaoTalk?
10. Should the system support English and Korean from the first version?

------

# 17. Recommended MVP Decision

For the first version, build a **single-clinic, mobile-responsive web app** with:

- Email/password login
- Staff roles
- Shift schedule
- Clock-in/out
- Leave request/approval
- Leave balance
- Correction request
- Monthly Excel export
- Audit log

Defer GPS, biometric integration, payroll integration, multi-branch support, and advanced labor-law automation until the product is stable in actual clinic use.

The product should prioritize simplicity, auditability, and reliable monthly reporting.
