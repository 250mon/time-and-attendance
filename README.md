# ClinicTime

Lightweight time-and-attendance and leave-management system for small clinics.

## Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Python 3.12+, SQLAlchemy, PostgreSQL
- **Infra:** Docker Compose

## Getting Started

These steps run the local development stack (`docker-compose.dev.yml`), with hot-reload and no reverse proxy. See [Deploying to a Linux Server](#deploying-to-a-linux-server) for the production stack.

1. Copy environment defaults:

   ```bash
   cp dev.env.example dev.env
   ```

2. Start all services:

   ```bash
   docker compose -f docker-compose.dev.yml --env-file dev.env up --build
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

These values come from `dev.env` (or `.env` in production). Change them before deploying to production:

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
| Lee Jaesung  | `jaesung@clinic.example` | `Sample123!` | 2025-06-13 | 8.8 days (proportional 2026 grant) |

These accounts demonstrate fiscal-year annual leave with legal-minimum adjustment (LSA Art. 60): monthly accrual in the hire year, proportional grant on the first January 1, regular grants thereafter, and `legal_adjustment` top-ups when fiscal grants fall below the hire-date legal minimum.

### Seeded leave types

Seven leave types are created automatically (Korean labor law and clinic defaults):

| Leave type | Max / request | Approval required |
|------------|---------------|-------------------|
| Annual Leave (연차휴가) | — (auto from hire date) | Yes |
| Sick Leave (병가) | No limit | Yes |
| Menstrual Leave (생리휴가) | 1 | Yes |
| Maternity Leave (출산전후휴가) | 90 | Yes |
| Paternity Leave (배우자 출산휴가) | 10 | Yes |
| Parental Leave (육아휴직) | 365 | Yes |
| Family Care Leave (가족돌봄휴가) | 10 | Yes |

> **To re-seed from scratch**, drop and recreate the database:
>
> ```bash
> docker compose -f docker-compose.dev.yml --env-file dev.env down -v   # removes the postgres volume
> docker compose -f docker-compose.dev.yml --env-file dev.env up --build
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
   - Set hire date on staff creation — annual leave is calculated automatically. Other leave types may limit days per request; total usage is recorded when leave is approved.
   - Leave allocations can also be adjusted later from the staff profile page.
4. Go to **Shifts** → create the shift templates your clinic uses (e.g. "Morning 09:00–18:00").
5. Go to **Schedules** → assign shifts to staff.
6. Staff can now clock in/out and submit leave requests.

### 5. Leave management

- **Admin/Manager view** (`/leave`): cards showing each staff member's annual leave allocated, used, and remaining for the current calendar year. Click a card to open the per-staff detail page (`/leave/staff/{id}`).
- **Staff view** (`/leave`): personal annual leave balance cards and a **Year** selector with calendar-year buttons from the hire year through the next calendar year (e.g. `2025`, `2026`, `2027`). Selecting a past year automatically backfills balance rows if they do not yet exist. Other leave types show days used only (no yearly allocation).
- **New request form**: lists all active leave types. Annual leave shows remaining days; other types show a per-request maximum when configured. Requests that exceed a non-annual per-request maximum are allowed but flagged with a warning to staff and managers.
- **Leave requests** (`/leave/requests`): lists requests with status, staff name, remaining annual balance, and policy-warning badges for over-max non-annual requests. Managers can approve or reject pending requests (they cannot approve their own).
- **Staff profile** (`/staff/{id}`): shows current-year annual leave balance and allows manual balance adjustments. Annual leave is assigned automatically from the hire date; other leave types are usage-only.
- **Leave types** (`/leave/types`): annual leave (`tenure_based`) is calculated from hire date. Other types use `default_days_per_year` as a **max days per single request** (blank = no limit), not a yearly cap.

#### Annual leave calculation

Annual leave uses a dual-track engine (Korean LSA Art. 60 + fiscal-year bulk grant):

| Track | Basis | Rules |
|-------|-------|-------|
| Legal minimum | Hire-date anniversary | 1 day/month in first year (max 11); 15 days at 1-year anniversary; +1 per 2 years after (max 25) |
| Fiscal policy | Calendar/fiscal year (default Jan 1) | Monthly accrual in hire year; proportional grant on first Jan 1; regular grants thereafter |
| `legal_adjustment` | Top-up | Applied when fiscal grants fall below legal minimum |

Before the 1-year hire anniversary, each calendar year's displayed balance counts **monthly accrual only** for that year. Fiscal grants and anniversary settlements are included once the anniversary has passed.

Configure via environment variables (see below).

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

Tests require a running PostgreSQL instance with a `clinic_time_test` database. The Docker Compose postgres service creates it automatically; for local runs use `docker compose -f docker-compose.dev.yml --env-file dev.env up postgres`.

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run lint
npm test
npm run build
```

## Configuring URLs, Ports, and the Database

### Application URLs

| Variable | Read by | Purpose |
|---|---|---|
| `FRONTEND_URL` | backend | The only origin allowed by CORS — must exactly match the URL the browser uses to load the app, including the port if one is in the address bar. |
| `NEXT_PUBLIC_BACKEND_URL` | frontend (browser) | Base URL the browser's JS uses for every API call (`lib/api-client.ts`). It's read when the frontend container starts (`npm run build`/`next dev`), so restart the frontend after changing it. |
| `BACKEND_URL` | — | Not currently read by application code; kept as a documented placeholder for the backend's public URL. |

How these are set differs between dev and prod because prod puts Caddy in front of both apps on one domain:

- **Local dev** (`docker-compose.dev.yml`, `dev.env`, no reverse proxy) — frontend and backend sit on separate host ports, so the URLs must include them, e.g. `FRONTEND_URL=http://localhost:3000`, `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`.
- **Production** (`docker-compose.yml`, `.env`, Caddy in front) — both are served from a single `DOMAIN` with path-based routing, so neither needs a port, and the backend URL gets an `/api` suffix that Caddy strips before forwarding internally: `FRONTEND_URL=https://yourdomain.com`, `NEXT_PUBLIC_BACKEND_URL=https://yourdomain.com/api`. This keeps the login cookie same-site (no `SameSite=None` workaround needed).

### Ports

| Variable | Used by | Default |
|---|---|---|
| `FRONTEND_PORT` | `docker-compose.dev.yml` | `3000` |
| `BACKEND_PORT` | `docker-compose.dev.yml` | `8000` |
| `HTTP_PORT` | `docker-compose.yml` (Caddy) | `80` |
| `HTTPS_PORT` | `docker-compose.yml` (Caddy) | `443` |

These only change the **host-side** port mapping; the containers always listen on their standard internal ports.

### Database

`DATABASE_URL` can be set in `.env`/`dev.env` to point at any reachable PostgreSQL instance — a managed database, a different host, a non-default port, etc. When set, it takes precedence over the bundled `postgres` service entirely. Leave it unset (or matching `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`) to use the `postgres` container Docker Compose starts for you.

### Annual leave configuration

| Variable | Default | Purpose |
|---|---|---|
| `LEAVE_FISCAL_START_MONTH` | `1` | Month the fiscal year starts (1 = January) |
| `LEAVE_FISCAL_START_DAY` | `1` | Day the fiscal year starts |
| `LEAVE_FISCAL_ROUNDING` | `round_2` | Rounding for fiscal proration: `none`, `floor`, `ceil`, `half_up`, `round_2` |
| `LEAVE_ADJUSTMENT_MODE` | `anniversary_top_up` | When to apply legal top-ups: `anniversary_top_up`, `termination_only`, or `none` |

Implementation: `backend/app/core/leave_accrual.py` (engine), `backend/app/core/kr_labor.py` (calendar-year facade).

## Deploying to a Linux Server

Production uses `docker-compose.yml`, which adds a [Caddy](https://caddyserver.com/) reverse proxy in front of the app. Caddy terminates TLS (automatic Let's Encrypt certificates) and routes by path on a single domain: `/api/*` → backend, everything else → frontend. Only Caddy's ports (80/443) are exposed to the host; the frontend and backend containers are reachable only on the internal Docker network.

1. **Point DNS at the server.** Create an A (or AAAA) record for your domain pointing at the server's public IP.

2. **Open firewall ports 80 and 443** (and 22 for SSH). Do not expose 3000, 8000, or 5432 publicly.

3. **Copy and configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Set at minimum:

   ```dotenv
   DOMAIN=yourdomain.com
   FRONTEND_URL=https://yourdomain.com
   BACKEND_URL=https://yourdomain.com/api
   NEXT_PUBLIC_BACKEND_URL=https://yourdomain.com/api
   COOKIE_SECURE=true
   BACKEND_SECRET_KEY=<long random secret>
   POSTGRES_PASSWORD=<strong password>
   SEED_ADMIN_EMAIL=<your admin email>
   SEED_ADMIN_PASSWORD=<strong password>
   ```

4. **Build and start the stack:**

   ```bash
   docker compose up --build -d
   ```

   Caddy automatically requests and renews a Let's Encrypt certificate for `DOMAIN` on first start — no certbot or manual cert setup needed. Alembic migrations run automatically as part of the backend's startup command.

5. **Verify:**
   - `https://yourdomain.com` — frontend
   - `https://yourdomain.com/api/health` — backend health check

To change which host ports Caddy listens on (e.g. behind another proxy/load balancer), set `HTTP_PORT`/`HTTPS_PORT` in `.env`. For local dev, `FRONTEND_PORT`/`BACKEND_PORT` in `dev.env` control the host-side port mapping in `docker-compose.dev.yml`.

## Project Layout

```text
backend/     FastAPI application, Alembic migrations, tests
frontend/    Next.js application
infra/       Caddy reverse-proxy config and backup scripts (deployment)
docs/        Product and implementation documentation
```

## Documentation

- [Product Requirements](docs/1_PRD.md)
- [Development Guide](docs/2_DevelopmentGuide.md)
- [Backlog](docs/3_Backlog.md)
- [Implementation Plan](docs/4_ImplementationPlan.md)
