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

## Configuring URLs, Ports, and the Database

### Application URLs

| Variable | Read by | Purpose |
|---|---|---|
| `FRONTEND_URL` | backend | The only origin allowed by CORS — must exactly match the URL the browser uses to load the app, including the port if one is in the address bar. |
| `NEXT_PUBLIC_BACKEND_URL` | frontend (browser) | Base URL the browser's JS uses for every API call (`lib/api-client.ts`). It's read when the frontend container starts (`npm run build`/`next dev`), so restart the frontend after changing it. |
| `BACKEND_URL` | — | Not currently read by application code; kept as a documented placeholder for the backend's public URL. |

How these are set differs between dev and prod because prod puts Caddy in front of both apps on one domain:

- **Local dev** (`docker-compose.yml`, no reverse proxy) — frontend and backend sit on separate host ports, so the URLs must include them, e.g. `FRONTEND_URL=http://localhost:3000`, `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`.
- **Production** (`docker-compose.prod.yml`, Caddy in front) — both are served from a single `DOMAIN` with path-based routing, so neither needs a port, and the backend URL gets an `/api` suffix that Caddy strips before forwarding internally: `FRONTEND_URL=https://yourdomain.com`, `NEXT_PUBLIC_BACKEND_URL=https://yourdomain.com/api`. This keeps the login cookie same-site (no `SameSite=None` workaround needed).

### Ports

| Variable | Used by | Default |
|---|---|---|
| `FRONTEND_PORT` | `docker-compose.yml` (dev) | `3000` |
| `BACKEND_PORT` | `docker-compose.yml` (dev) | `8000` |
| `HTTP_PORT` | `docker-compose.prod.yml` (Caddy) | `80` |
| `HTTPS_PORT` | `docker-compose.prod.yml` (Caddy) | `443` |

These only change the **host-side** port mapping; the containers always listen on their standard internal ports.

### Database

`DATABASE_URL` can be set in `.env` to point at any reachable PostgreSQL instance — a managed database, a different host, a non-default port, etc. When set, it takes precedence over the bundled `postgres` service entirely. Leave it unset (or matching `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`) to use the `postgres` container Docker Compose starts for you.

## Deploying to a Linux Server

Production uses `docker-compose.prod.yml`, which adds a [Caddy](https://caddyserver.com/) reverse proxy in front of the app. Caddy terminates TLS (automatic Let's Encrypt certificates) and routes by path on a single domain: `/api/*` → backend, everything else → frontend. Only Caddy's ports (80/443) are exposed to the host; the frontend and backend containers are reachable only on the internal Docker network.

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
   docker compose -f docker-compose.prod.yml up --build -d
   ```

   Caddy automatically requests and renews a Let's Encrypt certificate for `DOMAIN` on first start — no certbot or manual cert setup needed. Alembic migrations run automatically as part of the backend's startup command.

5. **Verify:**
   - `https://yourdomain.com` — frontend
   - `https://yourdomain.com/api/health` — backend health check

To change which host ports Caddy listens on (e.g. behind another proxy/load balancer), set `HTTP_PORT`/`HTTPS_PORT` in `.env`. For local dev, `FRONTEND_PORT`/`BACKEND_PORT` in `.env` control the host-side port mapping in `docker-compose.yml`.

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
