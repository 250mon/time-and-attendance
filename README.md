# ClinicTime

Lightweight time-and-attendance and leave-management system for small clinics.

## Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Python 3.12+, SQLAlchemy, PostgreSQL
- **Infra:** Docker Compose

## Getting Started

1. Copy environment defaults:

   ```bash
   cp .env.example .env
   ```

2. Start all services:

   ```bash
   docker compose up --build
   ```

3. Open the app:
   - Frontend: http://localhost:3000
   - Backend health: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

## Seed Data

The backend seeds a default clinic, admin account, Korean labor law leave types, and two sample staff members automatically on first boot — no manual step required. Seeding is idempotent: if any user already exists it is skipped entirely.

### Default admin credentials

| Field    | Value               |
| -------- | ------------------- |
| Email    | `admin@danaul.ai`   |
| Password | `123456`            |
| Role     | Owner (full access) |

These values come from `.env`. Change them before deploying to production:

```dotenv
SEED_CLINIC_NAME=My Clinic
SEED_ADMIN_EMAIL=admin@myclinic.com
SEED_ADMIN_PASSWORD=StrongPassword1!
SEED_ADMIN_NAME=Admin Name
```

### Sample staff

Two staff accounts are created on first boot for testing leave calculations. Their passwords are fixed and cannot be changed via env vars.

| Name         | Email                    | Password     | Hire date  | Annual leave (2026) |
|--------------|--------------------------|--------------|------------|----------------------|
| Kim Minji    | `minji@clinic.example`   | `Sample123!` | 2024-06-13 | 15 days (2 years)    |
| Lee Jaesung  | `jaesung@clinic.example` | `Sample123!` | 2025-06-13 | 11 days (1 year)     |

These accounts demonstrate tenure-based annual leave under Korean Labor Standards Act Art. 60: sub-1-year workers accrue 1 day per completed month (recalculated live), and workers with 1+ year receive 15 days base.

### Seeded leave types

Six leave types are created automatically based on Korean labor law:

| Leave type              | Days/year | Allocation          | Approval required |
|-------------------------|-----------|---------------------|-------------------|
| Annual Leave (연차휴가)   | —         | Auto from hire date | Yes               |
| Sick Leave (병가)        | 3         | Fixed               | Yes               |
| Maternity Leave (출산휴가) | 90       | Fixed               | Yes               |
| Paternity Leave (배우자 출산휴가) | 10 | Fixed              | Yes               |
| Family Care Leave (가족돌봄휴가) | 10 | Fixed             | Yes               |
| Public Holiday (공휴일)   | 0         | Fixed               | No                |

> **To re-seed from scratch**, drop and recreate the database:
>
> ```bash
> docker compose down -v   # removes the postgres volume
> docker compose up --build
> ```

## Using the App

### 1. Log in

Navigate to http://localhost:3000. You will be redirected to the login page. Use the seeded admin credentials (or any active account you have created).

### 2. Roles

| Role    | What they can do                                             |
|---------|--------------------------------------------------------------|
| Owner   | Full access — all sections, can deactivate/terminate staff   |
| Admin   | Same as Owner                                                |
| Manager | Can manage staff records and leave, cannot deactivate staff  |
| Staff   | Personal attendance and leave only                           |

### 3. Navigation

| Section       | Visible to              | Purpose                                                   |
|---------------|-------------------------|-----------------------------------------------------------|
| Dashboard     | All                     | Overview of today's attendance and pending requests        |
| Staff         | Owner / Admin / Manager | Create, view, edit, and deactivate staff accounts          |
| Shifts        | Owner / Admin / Manager | Define shift templates (start/end time, break rules)       |
| Schedules     | Owner / Admin / Manager | Assign shifts to staff members by date range               |
| Attendance    | All                     | Clock-in/out records and daily summaries                   |
| Leave         | All                     | Admin/Manager: overview of all staff leave; Staff: own leave balances and requests |
| Leave Types   | Owner / Admin / Manager | Create and manage leave type definitions                   |
| Leave Requests| All                     | Submit new requests; Admin/Manager can approve or reject   |
| Reports       | Owner / Admin / Manager | Export attendance and leave summaries                      |
| Audit Log     | Owner / Admin           | Immutable log of approvals, adjustments, and lock events   |
| Settings      | Owner / Admin           | Clinic profile and system configuration                    |

### 4. Typical first-time setup

1. **Log in** as Owner/Admin.
2. Go to **Leave Types** → review the seeded Korean labor law types. Add or adjust any clinic-specific types.
3. Go to **Staff** → add your clinic's staff members.
   - During creation, choose which leave types apply to each staff member. Tenure-based annual leave is calculated automatically from the hire date.
   - Leave allocations can also be adjusted later from the staff profile page.
4. Go to **Shifts** → create the shift templates your clinic uses (e.g. "Morning 09:00–18:00").
5. Go to **Schedules** → assign shifts to staff.
6. Staff can now clock in/out and submit leave requests.

### 5. Leave management

- **Admin/Manager view** (`/leave`): cards showing each staff member's total allocated, used, and remaining days for the current year. Click a card to open a detail modal with a per-leave-type breakdown. The modal shows service-year buttons from the staff member's hire date up to the current year.
- **Staff view** (`/leave`): personal leave balance cards per leave type. The period selector shows service-year buttons starting from the hire date (e.g. `2024.6.13`, `2025.6.13`) rather than calendar years. Selecting a past period automatically backfills the balance rows for that year if they do not yet exist.
- **New request form**: the leave type dropdown only shows types assigned to the requesting staff member, with remaining days displayed per type.
- **Leave requests** (`/leave/requests`): lists all requests with status, staff name, and remaining balance. The table filters to the selected service period. Managers can approve or reject pending requests (they cannot approve their own).
- **Staff profile** (`/staff/{id}`): shows assigned leave types and current-year balances. Unassigned types can be added with an Add button. The title says "Assigned leave types" — assignment is permanent from the hire date, not year-specific.
- Annual leave for workers with less than one year of service recalculates automatically as each full month of service completes.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy app
uvicorn app.main:app --reload
```

Tests require a running PostgreSQL instance with a `clinic_time_test` database. The Docker Compose postgres service creates it automatically; for local runs use `docker compose up postgres`.

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run lint
npm test
npm run build
```

## Project Layout

```text
backend/     FastAPI application, Alembic migrations, tests
frontend/    Next.js application
infra/       Nginx and backup scripts (deployment)
docs/        Product and implementation documentation
```

## Documentation

- [Product Requirements](docs/1_PRD.md)
- [Development Guide](docs/2_DevelopmentGuide.md)
- [Backlog](docs/3_Backlog.md)
- [Implementation Plan](docs/4_ImplementationPlan.md)
