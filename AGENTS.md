# Repository Guidelines

## Project Structure & Module Organization

This repository contains planning documentation for ClinicTime, a small-clinic time, attendance, and leave-management system.

- `docs/1_PRD.md` defines product scope, personas, MVP requirements, and post-MVP boundaries.
- `docs/2_DevelopmentGuide.md` defines the technical stack, phases, and target monorepo layout.

When implementation begins, follow the planned structure from the development guide:

- `backend/` for FastAPI, SQLAlchemy, Alembic, and tests.
- `frontend/` for Next.js, React, TypeScript, components, hooks, and tests.
- `infra/` for Docker, Nginx, backup scripts, and deployment config.
- `.env.example` for documented configuration defaults only.

## Build, Test, and Development Commands

```bash
# Full local stack
cp dev.env.example dev.env
docker compose -f docker-compose.dev.yml --env-file dev.env up --build

# Backend
cd backend && pytest
cd backend && ruff check .
cd backend && mypy app

# Frontend
cd frontend && npm run dev
cd frontend && npm test
```

See `README.md` and `CLAUDE.md` for full command reference.

## Coding Style & Naming Conventions

Use Python 3.12+ for backend code and TypeScript for frontend code. Prefer names such as `attendance_record`, `leave_request`, `shift_schedule`, and `monthly_report`.

Backend modules use `snake_case`; Python classes and Pydantic schemas use `PascalCase`. Frontend components use `PascalCase`, hooks start with `use`, and route folders use lowercase path names such as `frontend/app/attendance/`.

Keep configuration in environment variables and mirror required keys in `.env.example`.

## Testing Guidelines

Place backend tests under `backend/tests/` and frontend tests near components or in a dedicated test folder. Name backend tests `test_*.py`; name frontend tests with `.test.ts` or `.test.tsx`.

Prioritize tests for authentication, role-based access control, attendance calculations, leave balance changes, audit logging, and monthly report exports. Include timezone-sensitive cases using the configured clinic timezone.

## Commit & Pull Request Guidelines

This directory is not currently a Git repository, so no historical convention is available. Use concise imperative commit messages, for example `Add attendance correction workflow` or `Document deployment environment variables`.

Pull requests should include a summary, linked issue or requirement, test evidence, and screenshots for UI changes. Call out migrations, new environment variables, and behavior affecting payroll exports or audit history.

## Security & Configuration Tips

Never commit real secrets, clinic employee data, payroll exports, or production database dumps. Keep `.env.example` safe and generic. Protect authentication, audit logs, and attendance edits as high-risk areas during review.
