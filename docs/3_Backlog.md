# Product Backlog

# ClinicTime MVP Backlog

This backlog translates the PRD and development guide into implementation-ready work. Priorities use `P0` for MVP-critical, `P1` for important MVP support, and `P2` for post-MVP or enhancement work.

## Backlog Status

- `Ready`: clear enough to estimate and implement.
- `Needs Detail`: requires design, policy, or technical decisions.
- `Blocked`: depends on earlier foundation work.
- `Done`: implemented and verified.

## Phase 0: Project Foundation

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-001 | P0 | Ready | Create monorepo structure | Add `backend/`, `frontend/`, `infra/`, root README, and `.env.example`. |
| CT-002 | P0 | Ready | Configure Docker Compose | Start frontend, backend, and PostgreSQL with local defaults. |
| CT-003 | P0 | Ready | Bootstrap FastAPI backend | Add app structure, health endpoint, config loader, database session, linting, and tests. |
| CT-004 | P0 | Ready | Bootstrap Next.js frontend | Add app routes, shared layout, API client, form validation setup, and basic styling. |
| CT-005 | P1 | Ready | Add CI checks | Run backend tests, linting, type checks, and frontend checks on pull requests. |

## Phase 1: Authentication and Staff Management

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-101 | P0 | Blocked | Implement user and clinic models | Support roles, employment types, status, timestamps, and clinic timezone. |
| CT-102 | P0 | Blocked | Implement login/logout/session flow | Users can log in, log out, view `/auth/me`, and change password. |
| CT-103 | P0 | Blocked | Enforce role-based permissions | Staff cannot access admin pages or other staff private records. |
| CT-104 | P0 | Blocked | Build staff CRUD | Admin can create, edit, view, and deactivate staff without deleting history. |
| CT-105 | P1 | Blocked | Build login, dashboard, and staff pages | Include protected routing and role-appropriate navigation. |

## Phase 2: Shift and Schedule Management

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-201 | P0 | Blocked | Implement shift templates | Support start/end time, break minutes, active flag, and overnight shifts. |
| CT-202 | P0 | Blocked | Implement staff schedules | Assign shifts by staff, date, date range, and weekday pattern. |
| CT-203 | P1 | Blocked | Build schedule calendar UI | Managers can filter by staff and date range; staff can view own schedule. |

## Phase 3: Clock-In and Clock-Out

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-301 | P0 | Blocked | Store immutable attendance punches | Capture user, punch type, timestamp, source, IP address, and device info. |
| CT-302 | P0 | Blocked | Implement clock-in/out APIs | Prevent duplicate clock-in and clock-out without active session. |
| CT-303 | P0 | Blocked | Build staff attendance screen | Show today’s schedule, status, last punch, and clock action. |

## Phase 4: Attendance Calculation

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-401 | P0 | Blocked | Create attendance day summaries | Store scheduled, actual, regular, overtime, late, early-leave, and status fields. |
| CT-402 | P0 | Blocked | Implement recalculation service | Recalculate from schedules, raw punches, leave, and approved corrections. |
| CT-403 | P1 | Blocked | Add exception dashboard data | Surface late, absent, missing punch, working, completed, and leave states. |

## Phase 5: Correction Request Workflow

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-501 | P0 | Blocked | Submit attendance correction requests | Staff can request corrected times with work date and reason. |
| CT-502 | P0 | Blocked | Approve or reject corrections | Managers/admins can decide requests; approvals update summaries. |
| CT-503 | P1 | Blocked | Display correction history | Original punches remain visible and unchanged. |

## Phase 6: Leave Management

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-601 | P0 | Done | Configure leave types | Annual (`tenure_based`) and non-annual types with per-request max. |
| CT-602 | P0 | Done | Submit leave requests | Staff select type, date range, reason; over-max non-annual warns instead of blocking. |
| CT-603 | P0 | Done | Approve or reject leave | Managers see pending requests, balance, and policy warnings. |
| CT-604 | P1 | Blocked | Show team leave calendar | Approved leave appears in schedule and attendance views. |
| CT-605 | P0 | Blocked | Add historical leave entry | Admin can manually add past approved leave for existing employees during initial setup. |
| CT-606 | P0 | Blocked | Import historical leave CSV | Admin can upload CSV, preview row-level validation errors, and commit valid historical leave records. |

## Phase 7: Leave Balance Engine

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-701 | P0 | Done | Track annual leave balance | Calendar-year balances from dual-track accrual engine; usage-only for non-annual types. |
| CT-702 | P0 | Done | Deduct approved leave | Annual leave deducts balance; non-annual records usage; rejected leave does not deduct. |
| CT-703 | P1 | Done | Add manual balance adjustments | Admin adjustment requires reason and audit entry (annual leave only). |
| CT-704 | P0 | Blocked | Set opening leave balances | Admin can set initial balances for existing employees and audit each change. |

## Phase 8: Reports and Exports

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-801 | P0 | Blocked | Build monthly attendance report | Filter by staff, date, role, and employment type. |
| CT-802 | P0 | Blocked | Export CSV and Excel payroll data | Exported values match on-screen report totals. |
| CT-803 | P1 | Blocked | Add exception reports | Include late, early-leave, overtime, missing-punch, and leave usage reports. |

## Phase 9: Monthly Closing and Audit Log

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-901 | P0 | Blocked | Implement audit log | Record actor, action, entity, previous value, new value, reason, and timestamp. |
| CT-902 | P0 | Blocked | Lock and unlock monthly records | Admin can lock after review; unlock requires reason and audit entry. |
| CT-903 | P1 | Blocked | Warn before monthly lock | Show missing punches, pending corrections, pending leave, and unresolved issues. |

## Phase 10: Testing, Deployment, and Hardening

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-1001 | P0 | Blocked | Add core workflow tests | Cover auth, permissions, clock-in/out, correction, leave approval, and exports. |
| CT-1002 | P0 | Blocked | Add timezone-sensitive tests | Verify calculations for `CLINIC_TIMEZONE`, overnight shifts, and month boundaries. |
| CT-1003 | P1 | Blocked | Add backup and deployment docs | Include daily backup process and Docker Compose production notes. |
| CT-1004 | P1 | Blocked | Security hardening review | Verify password hashing, server-side RBAC, secret handling, and audit coverage. |

## Post-MVP Backlog

| ID | Priority | Status | Item | Acceptance Notes |
| --- | --- | --- | --- | --- |
| CT-2001 | P2 | Needs Detail | GPS-based clock-in | Disabled by default and privacy-reviewed before release. |
| CT-2002 | P2 | Needs Detail | QR-code clock-in | Requires QR lifecycle, expiration, and abuse prevention design. |
| CT-2003 | P2 | Needs Detail | Clinic Wi-Fi/IP restriction | Validate network boundaries without blocking legitimate users unexpectedly. |
| CT-2004 | P2 | Needs Detail | Notifications | Support reminders and approval notifications by email, SMS, or KakaoTalk. |
| CT-2005 | P2 | Needs Detail | Public holiday calendar integration | Sync holidays into schedules and attendance calculations. |
| CT-2006 | P2 | Needs Detail | Multi-branch support | Extend clinic, role, schedule, and reporting models for branch separation. |
