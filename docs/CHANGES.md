# LifeOps v1 – changes

Every file added or changed compared with the original folder. Generated caches
(`__pycache__`, `node_modules`, `.venv`, `dist`) are not listed.

## Root
- `.gitignore` – **added**. Ignores Python caches, `.venv`, `node_modules`, `dist`, `.env` (but keeps `.env.example`), editor files.
- `README.md` – **added**. What LifeOps is, architecture, running locally, env vars, API, upgrade/stamp steps, backend tour, DevOps milestones.
- `docker-compose.yml` – **changed**. Added a `pg_isready` healthcheck to the postgres service only. No new services.
- `docs/CHANGES.md` – **added**. This file.

## Backend – removed
- `backend/app/__pycache__/`, `backend/app/{models,routers,schemas}/__pycache__/` – **removed**. Compiled bytecode that shouldn't be in source.

## Backend – config, app wiring
- `backend/.env.example` – **added**. Every backend setting, documented.
- `backend/pyproject.toml` – **added**. Ruff and pytest configuration.
- `backend/requirements.txt` – **changed**. Original pins kept. Added alembic, bcrypt, PyJWT, httpx (+ httpcore, certifi), Mako, MarkupSafe, tzdata.
- `backend/requirements-dev.txt` – **added**. `-r requirements.txt` plus pytest, ruff and their deps.
- `backend/app/config.py` – **added**. Settings read from env / `.env` via python-dotenv.
- `backend/app/database.py` – **changed**. `DATABASE_URL` comes from settings instead of being hardcoded. Added `pool_pre_ping`.
- `backend/app/main.py` – **changed**. Removed `create_all`. CORS origins come from settings. Mounts all routers, with auth on protected ones.
- `backend/app/auth.py` – **added**. bcrypt password check, JWT create/verify, `require_auth` dependency, startup config check.

## Backend – models
- `backend/app/models/__init__.py` – **changed**. Imports every model so Alembic sees all tables.
- `backend/app/models/weight.py` – **changed (whitespace only)**. Trailing newline added by ruff.
- `backend/app/models/weight_goal.py` – **changed (whitespace only)**. Trailing newline added by ruff.
- `backend/app/models/money.py` – **added**. Accounts, categories, transactions, budgets, recurring bills, debts (Numeric money).
- `backend/app/models/calendar.py` – **added**. Events and tasks.
- `backend/app/models/invest.py` – **added**. Holdings and watchlist.
- `backend/app/models/career.py` – **added**. Job applications, interviews, contacts, certifications.

## Backend – schemas
- `backend/app/schemas/health.py` – **changed (whitespace only)**. Ruff blank-line/newline fixes. No field changes.
- `backend/app/schemas/common.py` – **added**. Shared `Money` type (Decimal in, JSON number out) and ORM base config.
- `backend/app/schemas/money.py` – **added**. Money request/response models, payoff and summary shapes.
- `backend/app/schemas/calendar.py` – **added**. Event/task models and agenda shapes.
- `backend/app/schemas/invest.py` – **added**. Holding/watchlist/quote/portfolio models.
- `backend/app/schemas/career.py` – **added**. Application/interview/contact/certification models and pipeline summary.
- `backend/app/schemas/auth.py` – **added**. Login request and token response.

## Backend – routers
- `backend/app/routers/health.py` – **changed (whitespace only)**. Trailing newline. Endpoints and behavior unchanged.
- `backend/app/routers/system.py` – **added**. `GET /healthz`, `GET /readyz`.
- `backend/app/routers/auth.py` – **added**. `GET /auth/config`, `POST /auth/login`, `GET /auth/me`.
- `backend/app/routers/money.py` – **added**. `/money/*` CRUD, budget copy, debt payoff projection, monthly summary.
- `backend/app/routers/calendar.py` – **added**. `/calendar/*` CRUD, task completion with recurrence, agenda and upcoming.
- `backend/app/routers/invest.py` – **added**. `/invest/*` CRUD, portfolio, quotes, priced watchlist.
- `backend/app/routers/career.py` – **added**. `/career/*` CRUD and pipeline summary.
- `backend/app/routers/dashboard.py` – **added**. `GET /dashboard` combining every module.

## Backend – services
- `backend/app/services/__init__.py` – **added**. Package marker.
- `backend/app/services/crud.py` – **added**. `get_or_404` and partial-update helper.
- `backend/app/services/dates.py` – **added**. Today/now in `APP_TIMEZONE`, month/week bounds, month arithmetic.
- `backend/app/services/money.py` – **added**. Bill due dates, debt payoff simulation, monthly summary.
- `backend/app/services/calendar.py` – **added**. Task recurrence and agenda building.
- `backend/app/services/market_data.py` – **added**. Twelve Data + CoinGecko clients with timeouts, TTL cache, `price_status`.
- `backend/app/services/portfolio.py` – **added**. Portfolio math (value, cost basis, gain/loss, allocation).

## Backend – migrations
- `backend/alembic.ini` – **added**. Alembic config (URL comes from settings, not this file).
- `backend/alembic/env.py` – **added**. Uses `Base.metadata` and `DATABASE_URL`.
- `backend/alembic/script.py.mako` – **added**. Template for new revisions.
- `backend/alembic/versions/0001_health_tables.py` – **added**. Exactly the original `weight_entries` and `weight_goals` tables (safe to `stamp`).
- `backend/alembic/versions/0002_lifeops_modules.py` – **added**. The 14 Money/Calendar/Invest/Career tables.

## Backend – scripts
- `backend/scripts/seed.py` – **added**. Optional `[SAMPLE]` data for every module. Refuses to run on a non-empty DB without `--force`.
- `backend/scripts/hash_password.py` – **added**. Prints a bcrypt hash for `APP_PASSWORD_HASH`.

## Backend – tests
- `backend/tests/__init__.py` – **added**. Package marker.
- `backend/tests/conftest.py` – **added**. Test DB lifecycle (create, migrate, truncate, drop), client, fake market data, auth fixture.
- `backend/tests/helpers.py` – **added**. Create/drop database and Alembic config helpers.
- `backend/tests/test_system.py` – **added**. Root, healthz, readyz.
- `backend/tests/test_health.py` – **added**. Weight CRUD and goal rules (one active, activate/complete, progress).
- `backend/tests/test_money.py` – **added**. Money CRUD, filters, budgets, bills, payoff math, monthly summary.
- `backend/tests/test_calendar.py` – **added**. Events/tasks CRUD, recurrence, agenda, upcoming.
- `backend/tests/test_invest.py` – **added**. Holdings/watchlist CRUD, portfolio math, market-data client with mocked HTTP.
- `backend/tests/test_career.py` – **added**. Career CRUD, cascades, pipeline summary.
- `backend/tests/test_dashboard.py` – **added**. Dashboard with data, empty, and missing prices.
- `backend/tests/test_auth.py` – **added**. Auth disabled/enabled, login, token checks, public routes.
- `backend/tests/test_migrations.py` – **added**. Upgrade on an empty DB, downgrade/upgrade, stamp-then-upgrade on original tables.

## Frontend – config
- `frontend/.env.example` – **added**. `VITE_API_URL`.
- `frontend/package.json` / `package-lock.json` – **changed**. Added `react-router` (v7, supports Node 20).
- `frontend/index.html` – **changed**. Title is now "LifeOps".
- `frontend/src/vite-env.d.ts` – **added**. Types for `import.meta.env.VITE_API_URL`.

## Frontend – app shell
- `frontend/src/App.tsx` – **changed**. Was the single-page Health UI. Now holds the routes (sidebar layout, lazy-loaded pages, login). The Health UI moved to `pages/Health.tsx`.
- `frontend/src/Layout.css` – **added**. Sidebar layout, tables, forms, tabs, badges, login. Original `App.css` is unchanged.

## Frontend – API client
- `frontend/src/api/client.ts` – **added**. fetch wrapper: base URL, JSON, JWT header, errors, 401 handling.
- `frontend/src/api/types.ts` – **added**. TypeScript types for every API shape.
- `frontend/src/api/crud.ts` – **added**. Generic list/create/update/delete helper.
- `frontend/src/api/health.ts` – **added**. Health endpoints (original paths).
- `frontend/src/api/money.ts` – **added**. Money endpoints.
- `frontend/src/api/calendar.ts` – **added**. Calendar endpoints.
- `frontend/src/api/invest.ts` – **added**. Invest endpoints.
- `frontend/src/api/career.ts` – **added**. Career endpoints.
- `frontend/src/api/dashboard.ts` – **added**. Dashboard endpoint.
- `frontend/src/api/auth.ts` – **added**. Auth config/login/me.

## Frontend – auth, hooks, utils
- `frontend/src/auth/AuthContext.ts` – **added**. Auth context definition.
- `frontend/src/auth/AuthProvider.tsx` – **added**. Reads `/auth/config`, stores the token, handles logout/401.
- `frontend/src/auth/useAuth.ts` – **added**. Hook to read auth state.
- `frontend/src/hooks/useApiData.ts` – **added**. Load/reload/error state for API calls.
- `frontend/src/utils/format.ts` – **added**. Money/date/percent formatting.
- `frontend/src/utils/forms.ts` – **added**. Field definitions and form ↔ payload conversion.

## Frontend – components
- `frontend/src/components/Layout.tsx` – **added**. Sidebar navigation, API status indicator, logout.
- `frontend/src/components/RequireAuth.tsx` – **added**. Redirects to `/login` when auth is on and there's no token.
- `frontend/src/components/ResourceManager.tsx` – **added**. Reusable table + create/edit/delete forms.
- `frontend/src/components/FormFields.tsx` – **added**. Renders inputs/selects/textareas from field definitions.
- `frontend/src/components/Alert.tsx` – **added**. Success/error/info messages.
- `frontend/src/components/StatCard.tsx` – **added**. Summary number card.
- `frontend/src/components/PageHeader.tsx` – **added**. Page title block.
- `frontend/src/components/Tabs.tsx` – **added**. Simple tab switcher.
- `frontend/src/components/Badge.tsx` – **added**. Status/priority pill.
- `frontend/src/components/SpendingChart.tsx` – **added**. Spending vs budget bar chart (recharts).
- `frontend/src/components/AllocationChart.tsx` – **added**. Portfolio allocation pie chart (recharts).
- `frontend/src/components/health/ActiveGoalSummary.tsx` – **added**. Active goal card, stats and progress bar (from the original App.tsx).
- `frontend/src/components/health/WeightChart.tsx` – **added**. Weight trend chart (from the original App.tsx).
- `frontend/src/components/health/RecordWeightForm.tsx` – **added**. Record-weight form (from the original App.tsx).
- `frontend/src/components/health/CreateGoalForm.tsx` – **added**. Create-goal form (from the original App.tsx).
- `frontend/src/components/health/GoalList.tsx` – **added**. Goal list (from the original App.tsx).
- `frontend/src/components/health/GoalRow.tsx` – **added**. One goal with edit/activate/complete/delete (from the original App.tsx).
- `frontend/src/components/health/WeightList.tsx` – **added**. Weight history with edit/delete (from the original App.tsx).

## Frontend – pages
- `frontend/src/pages/Health.tsx` – **added**. The original Health page logic, now built from components.
- `frontend/src/pages/Dashboard.tsx` – **added**. Overview of all modules.
- `frontend/src/pages/Money.tsx` – **added**. Money page with tabs.
- `frontend/src/pages/money/OverviewTab.tsx` – **added**. Monthly summary + spending chart.
- `frontend/src/pages/money/TransactionsTab.tsx` – **added**. Transactions with filters.
- `frontend/src/pages/money/BudgetsTab.tsx` – **added**. Monthly budgets + copy month.
- `frontend/src/pages/money/BillsTab.tsx` – **added**. Recurring bills.
- `frontend/src/pages/money/DebtsTab.tsx` – **added**. Debts + payoff calculator.
- `frontend/src/pages/money/SetupTab.tsx` – **added**. Accounts and categories.
- `frontend/src/pages/Calendar.tsx` – **added**. Agenda, events, tasks.
- `frontend/src/pages/Invest.tsx` – **added**. Portfolio summary, allocation chart, holdings, watchlist.
- `frontend/src/pages/Career.tsx` – **added**. Pipeline, applications, interviews, contacts, certifications.
- `frontend/src/pages/Login.tsx` – **added**. Login form (shown only when auth is enabled).
