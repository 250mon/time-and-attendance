# Multi-Tenant Implementation Plan

# ClinicTime — Multi-Clinic (Multi-Tenant) Support

This document defines how ClinicTime evolves from **single-clinic deployments** to **multi-tenant SaaS** while keeping a path for self-hosted single-clinic installs.

Related docs:

- [Product Requirements](1_PRD.md) — scope and personas
- [Development Guide](2_DevelopmentGuide.md) — technical patterns
- [Backlog](3_Backlog.md) — `CT-1101` through `CT-1110`
- [Implementation Plan](4_ImplementationPlan.md) — Phase 11

---

## 1. Implementation Status

MT-1 through MT-6 are fully implemented. The table below reflects the current (post-implementation) state.

| Layer | Status |
|-------|--------|
| **Database** | `clinics` table with `slug`, `status`, `timezone`; all domain rows have `clinic_id`; per-clinic `UNIQUE (clinic_id, email)` on users |
| **Backend services** | All queries filter by `actor.clinic_id`; JWT carries mandatory `cid` claim |
| **Frontend** | Clinic slug login, clinic name in app shell, Settings profile section, `/platform` admin UI |
| **Bootstrap** | `seed_default_clinic_and_admin` creates one clinic on first boot; `POST /clinics` creates additional clinics |
| **Auth** | Email + password + optional clinic slug; JWT `cid` claim enforced; suspended clinic rejects all requests |
| **Email uniqueness** | Per-clinic `UNIQUE (clinic_id, email)` — same email allowed across clinics |
| **Timezone** | `clinics.timezone` read per-request in all calculation paths; `CLINIC_TIMEZONE` env var is default only |
| **Clinic API** | `GET/PATCH /clinics/me`, `POST /clinics` (bootstrap), `GET /clinics/by-slug/{slug}` (public) |
| **Platform admin** | `POST /platform/clinics` (create), `GET /platform/clinics` (list), `GET /platform/metrics`, `POST /platform/clinics/{id}/suspend\|activate` |

### Classification

**Full multi-tenancy:** shared database, row-level isolation by `clinic_id`, multiple clinics per deployment supported.

---

## 2. Target Architecture

### Tenancy model

```text
Deployment (single Docker stack / single DB)
└── Clinic A (tenant)
│   ├── users, shifts, schedules, attendance, leave, audit …
└── Clinic B (tenant)
    └── …
```

- **One PostgreSQL database**, shared schema.
- **Every tenant-owned row** carries `clinic_id`; all reads/writes scoped to the authenticated user's clinic (or explicit platform-admin context).
- **No cross-clinic queries** in normal application code.

### Tenant identity

Each clinic gets a stable **`slug`** (URL-safe identifier), e.g. `seoul-dental`, used for:

- Login context: `POST /auth/login` includes `clinic_slug` **or** subdomain `{slug}.clinictime.app`
- Optional future: path prefix `/c/{slug}/…` on frontend

Recommended MVP for multi-tenant login: **clinic slug on login form** (simplest; works behind one domain).

**Slug validation rule:** `^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$` — lowercase alphanumeric, hyphens allowed in the middle, 3–64 characters. Enforce on `POST /clinics` and in the Alembic backfill for the seed clinic. Reserved words to reject: `api`, `admin`, `www`, `health`, `me`, `demo`.

### Roles (unchanged within tenant)

```text
OWNER | ADMIN | MANAGER | STAFF   — scoped to one clinic_id
```

Optional later: **`PLATFORM_ADMIN`** for operator staff (list clinics, suspend tenant) — not required for first multi-tenant release.

---

## 3. Design Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Tenancy style | Shared DB + `clinic_id` | Already in schema; fits small-clinic scale |
| D2 | Email uniqueness | **Per clinic** `(clinic_id, email)` | Same person may work at two clinics with one email |
| D3 | Tenant resolution | Clinic slug at login | No DNS/subdomain setup required for MVP |
| D4 | Self-service signup | **Invite-only** for v1 | Admin creates clinic + owner; no public registration |
| D5 | Single-clinic installs | Keep seed path | `SEED_CLINIC_NAME` + one admin still works |
| D6 | Timezone | Read `clinics.timezone` per request | Replace global `settings.clinic_timezone` in calculation paths |
| D7 | OAuth (future) | Match user by `(clinic_id, email)` | Aligns with per-clinic email scope |
| D8 | JWT `clinic_id` claim | **Mandatory** `cid` claim in every token | Defense-in-depth: token from Clinic A is rejected by Clinic B even if service-layer filtering has a bug |

---

## 4. Data Model Changes

### 4.1 `clinics` table — add columns

```text
slug          VARCHAR(64)  NOT NULL UNIQUE   -- e.g. seoul-dental
status        ENUM         ACTIVE | SUSPENDED
contact_email VARCHAR(255) nullable          -- clinic owner contact
```

### 4.2 `users` table — constraint change

```sql
-- Drop:  UNIQUE (email)
-- Add:   UNIQUE (clinic_id, email)
```

Migration must handle existing single-clinic data (no conflict if one clinic).

### 4.3 Optional: `clinic_invitations`

For onboarding additional clinics without platform UI:

```text
id, clinic_id, email, role, token, expires_at, accepted_at, created_by
```

Defer if manual SQL + seed script is enough for early pilots.

---

## 5. API Changes

### 5.1 Clinic management (new)

| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| `POST` | `/clinics` | Platform admin *or* bootstrap secret | Create clinic + owner user |
| `GET` | `/clinics/me` | Authenticated user | Current clinic profile |
| `PATCH` | `/clinics/me` | OWNER / ADMIN | Update name, address, timezone |
| `GET` | `/clinics/by-slug/{slug}` | Public | Resolve slug for login UI (name, logo only) |

\* Platform admin can be a env-guarded bootstrap token initially: `CLINIC_BOOTSTRAP_SECRET`.

### 5.2 Authentication

| Change | Detail |
|--------|--------|
| Login request | Add `clinic_slug: str` (or derive from subdomain middleware) |
| Lookup | `(clinic_id from slug, email)` → verify password |
| JWT payload | **Mandatory** `cid` claim (`clinic_id`); `get_current_user` rejects tokens where `cid` ≠ `user.clinic_id` (see D8) |
| `/auth/me` | Include clinic summary `{ id, name, slug, timezone }` |
| Session invalidation | `get_current_user` must check `clinic.status == ACTIVE` on every request, not only at login — so suspending a clinic immediately invalidates in-flight sessions without waiting for token expiry |

### 5.3 Service layer audit

Every service method must:

1. Filter by `actor.clinic_id` on list/get/update.
2. On create, set `clinic_id = actor.clinic_id` (never from client body).
3. On fetch by ID, verify row's `clinic_id == actor.clinic_id`.

**Deliverable:** checklist + automated tests (`test_tenant_isolation.py`) covering staff, leave, attendance, reports, audit.

---

## 6. Backend Implementation Phases

### Phase MT-1: Schema and isolation hardening

- Alembic: `slug`, `status` on `clinics`; `(clinic_id, email)` unique on `users`.
- Migration pre-flight: assert no duplicate `(clinic_id, email)` rows exist before dropping the global `UNIQUE (email)` constraint; fail loudly rather than silently skip.
- Backfill `slug` for seeded clinic (e.g. from `SEED_CLINIC_SLUG` env); validate against slug regex (see §2).
- Embed mandatory `cid` (`clinic_id`) claim in JWT; update `create_access_token`, `decode_access_token`, and `get_current_user` (see D8 and §5.2).
- Fix any service/route missing `clinic_id` filter (grep audit).
- Add cross-tenant isolation tests.

### Phase MT-2: Per-clinic timezone

- Add `get_clinic_timezone(db, clinic_id) -> ZoneInfo`.
- Replace `settings.clinic_timezone` in:
  - `attendance_calculation_service`
  - `attendance_correction_service`
  - `report_service`
- Keep `CLINIC_TIMEZONE` as default only when creating new clinics.

### Phase MT-3: Clinic profile API

- `GET/PATCH /clinics/me`
- Settings UI: clinic name, timezone, address (extend `/settings`).

### Phase MT-4: Multi-clinic login

- Extend `LoginRequest` with `clinic_slug`.
- Login page: clinic slug field (or subdomain detection).
- Optional: remember last slug in `localStorage`.

### Phase MT-5: Clinic onboarding

- `POST /clinics` with bootstrap secret or platform role.
- Creates clinic, owner user, default leave types (reuse `seed_default_leave_types` logic per clinic).
- `seed_default_leave_types(db, clinic_id)` now lives in `bootstrap/leave_defaults.py` and accepts an explicit `clinic_id` — prerequisite satisfied during seeding refactor.
- Document operator runbook for adding tenants (see also §12 below on pre-MT-6 ops).

### Phase MT-6 (optional): Platform admin

- `PLATFORM_ADMIN` role or separate service account.
- List/suspend/create/edit clinics; view aggregate metrics.
- Defer until >10 tenants in production.

---

## 7. Frontend Changes

| Area | Change | Status |
|------|--------|--------|
| **Login** | Clinic slug input; validate slug via `GET /clinics/by-slug/{slug}` | ✅ done |
| **AuthProvider** | Store `clinic` object from `/auth/me` | ✅ done |
| **Settings** | Clinic profile section (name, timezone, address) | ✅ done |
| **App shell** | Show clinic name in header | ✅ done |
| **No clinic switcher** | Users belong to one clinic; switching = logout + different slug | ✅ done |
| **Platform admin** | Standalone `/platform` page: create clinic form, metrics, clinic list, suspend/activate | ✅ done |

---

## 8. Configuration

Environment variables (all implemented):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SEED_CLINIC_SLUG` | `demo` | Slug for the bootstrap clinic on first boot |
| `CLINIC_BOOTSTRAP_SECRET` | *(empty — disabled)* | Protects `POST /clinics`; set to enable onboarding |
| `MULTI_TENANT_ENABLED` | `false` | `true` = require slug at login; `false` = single-clinic mode |
| `NEXT_PUBLIC_MULTI_TENANT_ENABLED` | `false` | Mirror of above for the Next.js frontend build |
| `PLATFORM_ADMIN_SECRET` | *(empty — disabled)* | Protects `/platform` admin UI; set to enable |

Single-clinic mode preserves existing behavior for self-hosted deployments:

```text
MULTI_TENANT_ENABLED=false  →  login with email only; implicit single clinic
MULTI_TENANT_ENABLED=true   →  login requires clinic_slug
```

---

## 9. Migration Path for Existing Deployments

1. Run Alembic migration (add slug, fix email unique).
2. Set `SEED_CLINIC_SLUG` or migration backfill for existing clinic row.
3. Keep `MULTI_TENANT_ENABLED=false` until login UI is updated.
4. Enable multi-tenant mode; add slug field to login page.
5. No data loss; existing users remain on original `clinic_id`.

---

## 10. Testing Strategy

### Required tests

| Test | File | Status |
|------|------|--------|
| `test_login_requires_correct_clinic_slug` | `test_auth.py` | ✅ |
| `test_same_email_two_clinics` | `test_tenant_isolation.py` | ✅ |
| `test_staff_list_never_leaks_other_clinic` | `test_tenant_isolation.py` | ✅ |
| `test_leave_types_scoped_to_clinic` | `test_tenant_isolation.py` | ✅ |
| `test_attendance_punch_isolation` | — | ❌ missing |
| `test_cannot_access_resource_by_uuid_guessing` | `test_tenant_isolation.py` (staff only) | ⚠️ partial |
| `test_timezone_uses_clinic_not_global_env` | — | ❌ missing |

### Manual QA

1. Create clinic A and clinic B via `POST /clinics` with `CLINIC_BOOTSTRAP_SECRET`.
2. Create staff with same email in both → both can log in with respective slug.
3. Verify A's manager cannot see B's leave requests.
4. Suspend clinic A from `/platform` → clinic A users get 401; clinic B unaffected.

---

## 11. Security Checklist

- [x] Never accept `clinic_id` from client on create/update without verifying actor membership
- [x] JWT `cid` claim is mandatory; `get_current_user` rejects any token where `cid` ≠ `user.clinic_id`
- [x] JWT does not allow switching clinic without re-login
- [x] Audit logs include `clinic_id`
- [ ] Rate-limit login per `(slug, email)` tuple — not yet implemented
- [ ] Rate-limit `GET /clinics/by-slug/{slug}` — public endpoint, enumerable — not yet implemented
- [x] Suspend clinic → `get_current_user` checks `clinic.status` on every request; in-flight sessions rejected immediately
- [x] Cross-tenant IDOR tests in CI

---

## 12. Out of Scope (this plan)

These remain separate from multi-**tenant** (multi-**clinic** org) work:

- **Multi-branch** within one clinic (branch_id on schedules/reports) — see CT-2006
- **OAuth / SSO** — see auth plan; must use per-clinic email scope
- **Separate database per tenant** — not needed at current scale
- **Public self-service signup** — invite/bootstrap only for v1

### Operator runbook

- **Add a tenant:** use the **Create Clinic** form in the Platform Admin UI at `/platform`, or call `POST /platform/clinics` with `X-Platform-Token`, or call `POST /clinics` with `X-Bootstrap-Secret`.
- **Suspend/activate a tenant:** use the Platform Admin UI at `/platform`, or directly via SQL: `UPDATE clinics SET status = 'SUSPENDED' WHERE slug = '<slug>';` — takes effect on the next request.
- **Reset a user password / view audit logs for a clinic:** `psql` with an explicit `WHERE clinic_id = '<id>'` filter.

---

## 13. Definition of Done

**All items met as of MT-6.**

1. ✅ Two clinics can coexist in one database with isolated data.
2. ✅ Same email can exist in both clinics with independent passwords.
3. ✅ Login requires clinic slug (when `MULTI_TENANT_ENABLED=true`).
4. ✅ Attendance and leave calculations use each clinic's timezone from DB.
5. ✅ Clinic owner can edit clinic profile in Settings.
6. ✅ Cross-tenant isolation tests pass in CI.
7. ✅ README and `.env.example` document new variables and onboarding steps.

---

## 14. Implementation Order (completed)

| Phase | Description | Status |
|-------|-------------|--------|
| MT-1 | Schema + isolation hardening + JWT `cid` | ✅ done |
| MT-2 | Per-clinic timezone | ✅ done |
| MT-3 | Clinic profile API + Settings UI | ✅ done |
| MT-4 | Login with clinic slug + `MULTI_TENANT_ENABLED` flag | ✅ done |
| MT-5 | `POST /clinics` onboarding + operator docs | ✅ done |
| MT-6 | Platform admin UI (list/suspend/activate + metrics) | ✅ done |

Remaining open items: rate-limiting on login and `/clinics/by-slug/{slug}` (§11), two missing test cases (§10).
