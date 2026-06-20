# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClinicTime** — a time-and-attendance and leave-management system for small clinics. The monorepo contains a FastAPI backend (`backend/`), a Next.js 16 frontend (`frontend/`), and Docker Compose infrastructure.

Two Docker Compose stacks exist: `docker-compose.yml` is **production** (Caddy reverse proxy, env from `.env`) and is what plain `docker compose ...` targets by default. `docker-compose.dev.yml` is **local dev** (hot-reload, no proxy, separate frontend/backend ports, env from `dev.env`) and must be selected explicitly with `-f docker-compose.dev.yml --env-file dev.env`.

## Commands

### Full stack (Docker, local dev)

```bash
cp dev.env.example dev.env
docker compose -f docker-compose.dev.yml --env-file dev.env up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Default seed admin: `admin@clinic.example` / `ChangeMe123!` (set in `dev.env`)

### Full stack (Docker, production)

```bash
cp .env.example .env
docker compose up --build -d
```

Serves both apps behind Caddy on `HTTP_PORT`/`HTTPS_PORT` (see `.env`); see `README.md` for full deployment steps.

### Backend (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                         # all tests
pytest tests/test_auth.py      # single file
ruff check .                   # lint
mypy app                       # type-check (strict mode)
alembic upgrade head           # apply migrations
uvicorn app.main:app --reload  # dev server
```

Tests require a running PostgreSQL instance with a `clinic_time_test` database. The Docker Compose service (`infra/postgres/init-test-db.sh`) creates it automatically; for local runs, create it manually or `docker compose -f docker-compose.dev.yml --env-file dev.env up postgres`.

### Frontend (local)

```bash
cd frontend
npm install
npm run dev    # dev server on :3000
npm run lint
npm test       # Jest
npm run build
```

## Architecture

### Backend (`backend/app/`)

Layered FastAPI app — route handlers are thin; all business logic lives in services.

```
core/
  config.py       — Pydantic Settings from env vars
  security.py     — bcrypt password hashing, JWT (HS256) creation/decode
  permissions.py  — role/status guard helpers
api/
  deps.py         — FastAPI dependency: get_current_user, require_roles(*roles)
  routes/         — one file per resource (auth, staff, health, …)
models/           — SQLAlchemy 2.x ORM models; enums.py has UserRole/EmploymentType/UserStatus
schemas/          — Pydantic v2 request/response schemas
services/         — business logic (AuthService, StaffService, …)
db/
  session.py      — engine + SessionLocal + get_db dependency
  base.py         — declarative Base
```

**Authentication** uses HTTP-only cookies (`access_token`). `POST /auth/login` sets the cookie and returns the user object. All protected routes depend on `get_current_user`; role guards use `require_roles(UserRole.ADMIN, ...)`.

**Startup seed**: `app.main` lifespan calls `seed_default_clinic_and_admin` to create the demo clinic and admin on first boot (idempotent).

**Migrations**: Alembic, run `alembic upgrade head`. New models must be imported in `db/base.py` before generating revisions.

### Frontend (`frontend/`)

Next.js 16 App Router with React 19. **Read `node_modules/next/dist/docs/` before writing Next.js code** — this version has breaking changes from older releases.

```
app/
  (public)/login/   — unauthenticated login page + form
  (protected)/      — layout wraps all pages in RequireAuth + AppShell
    dashboard/, staff/, attendance/, leave/, schedules/, reports/, settings/
components/
  AuthProvider.tsx  — React context: user state, login/logout, hasRole(), canManageStaff, canDeactivateStaff
  RequireAuth.tsx   — redirects to /login if no authenticated user
  AppShell.tsx      — nav shell rendered around all protected pages
  PlaceholderPage.tsx — stub used for not-yet-implemented sections
lib/
  api-client.ts     — axios instance (withCredentials: true), typed API functions
  validation.ts     — Zod schemas shared across forms
hooks/
  useBackendHealth.ts
types/index.ts      — shared TypeScript types (User, UserRole, StaffCreateInput, …)
```

All API calls go through `lib/api-client.ts` using `withCredentials: true` so the session cookie is sent. Error messages are extracted via `getApiErrorMessage()`.

## Key Domain Rules (from `docs/2_DevelopmentGuide.md`)

- **Raw punch records are immutable.** Corrections go through an approval workflow and are applied at calculation time only.
- **Attendance recalculation is deterministic**: same inputs (schedule + punches + approved corrections + approved leave) always produce the same `attendance_days` row.
- **`DELETE /staff/{id}` deactivates, never deletes.**
- **Managers cannot approve their own leave or correction requests.**
- **Monthly locking** (`monthly_closings`) blocks all edits to that period's records.
- **Audit logging** is required for: corrections approved/rejected, leave approved/rejected, balance adjustments, month lock/unlock, report exports.

## Development Phase Status

The codebase has completed **Phase 0** (foundation) and **Phase 1** (auth + staff management). Remaining phases per `docs/2_DevelopmentGuide.md`:

2. Shift and schedule management
3. Clock-in / clock-out
4. Attendance calculation engine
5. Correction request workflow
6. Leave management
7. Leave balance engine
8. Reports and exports
9. Monthly closing and audit log
10. Testing, deployment, hardening

## Naming Conventions

- Python: `snake_case` modules and variables, `PascalCase` classes and Pydantic schemas
- TypeScript: `PascalCase` components, `camelCase` functions/variables, `use` prefix for hooks
- Route folders: lowercase path names (`app/attendance/`, `app/leave/`)
- Test files: `test_*.py` (backend), `*.test.ts` / `*.test.tsx` (frontend)

## Environment Variables

Key vars (see `.env.example` for production, `dev.env.example` for local dev):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string |
| `BACKEND_SECRET_KEY` | JWT signing secret |
| `NEXT_PUBLIC_BACKEND_URL` | Frontend → backend URL |
| `CLINIC_TIMEZONE` | Default `Asia/Seoul`; used in all time calculations |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | Bootstrap admin credentials |
