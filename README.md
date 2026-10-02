# LifeOps

LifeOps is my personal "operating system": one app for the parts of life I want
to track. It is single-user and runs locally.

| Module | What it does |
| --- | --- |
| **Health** | Weight log, weight goals (planned → active → completed), goal progress |
| **Money** | Accounts, categories, transactions, monthly budgets, recurring bills, debts + payoff projection, monthly summary |
| **Calendar** | Events, tasks (priority, status, simple daily/weekly/monthly recurrence), today / this-week agenda |
| **Invest** | Stock + crypto holdings, watchlist, live prices (Twelve Data / CoinGecko), portfolio summary |
| **Career** | Job applications, interviews, contacts, certifications / study goals, pipeline summary |
| **Dashboard** | One screen pulling together all of the above |

Stack: **FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL** for the API, and
**React + TypeScript + Vite + react-router + recharts** for the frontend.

---

## Architecture

```mermaid
flowchart LR
    Browser["Browser<br/>React SPA (Vite)"] -->|"HTTP + JSON<br/>(Bearer JWT when auth is on)"| API

    subgraph API["FastAPI app (backend/app)"]
        direction TB
        Routers["routers/<br/>health · money · calendar · invest · career · dashboard · auth · system"]
        Services["services/<br/>money math · agenda · portfolio · market data · dates"]
        Models["models/ (SQLAlchemy)<br/>schemas/ (Pydantic)"]
        Routers --> Services
        Routers --> Models
        Services --> Models
    end

    Models -->|"psycopg 3"| DB[("PostgreSQL 17")]
    Alembic["Alembic migrations"] -->|"schema changes"| DB
    Services -->|"httpx, 60s cache"| TD["Twelve Data<br/>(stock prices)"]
    Services -->|"httpx, 60s cache"| CG["CoinGecko Demo API<br/>(crypto prices)"]
```

Only the backend talks to the market-data APIs, so API keys never reach the browser.

---

## Project layout

```
lifeops/
├── docker-compose.yml        # PostgreSQL only
├── backend/
│   ├── app/
│   │   ├── main.py           # creates the FastAPI app, CORS, mounts routers
│   │   ├── config.py         # all settings, read from env / backend/.env
│   │   ├── database.py       # engine, SessionLocal, Base, get_db
│   │   ├── auth.py           # bcrypt + JWT helpers, require_auth dependency
│   │   ├── models/           # SQLAlchemy tables (one file per module)
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── routers/          # HTTP endpoints (one file per module)
│   │   └── services/         # logic that isn't HTTP (math, market data, dates)
│   ├── alembic/              # migrations (0001 = health tables, 0002 = new modules)
│   ├── scripts/              # seed.py, hash_password.py
│   ├── tests/                # pytest suite (runs against real Postgres)
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/              # typed API client, one file per module
│   │   ├── auth/             # login state (AuthProvider)
│   │   ├── components/       # Layout, ResourceManager, charts, health/*
│   │   ├── pages/            # Dashboard, Health, Money (+ money/*), Calendar, Invest, Career, Login
│   │   └── App.tsx           # routes
│   └── .env.example
└── docs/CHANGES.md           # every file added/changed in v1
```

---

## Run it locally

Prereqs: Python 3.14 (3.13 also works), Node 20+, Docker (just for Postgres).

### 1. Postgres

```bash
docker compose up -d postgres
```

### 2. Backend

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt     # or requirements.txt if you won't run tests
cp .env.example .env                    # then edit as needed

alembic upgrade head                    # fresh DB only (see "Existing DB" below)
python scripts/seed.py                  # optional: adds [SAMPLE] data
uvicorn app.main:app --reload
```

API at http://localhost:8000, interactive docs at http://localhost:8000/docs.

### 3. Frontend

```bash
cd frontend
cp .env.example .env                    # optional; defaults to http://localhost:8000
npm ci
npm run dev
```

App at http://localhost:5173.

### Useful commands

```bash
# backend/
ruff check .                            # lint
pytest                                  # tests (needs Postgres, see below)
alembic revision --autogenerate -m "describe change"   # after editing models
alembic upgrade head
alembic check                           # fails if models and migrations disagree
python scripts/hash_password.py         # bcrypt hash for APP_PASSWORD_HASH

# frontend/
npm run lint
npm run build                           # outputs dist/
```

---

## Applying this version over my existing folder

1. Back up the current folder (or make sure my work is committed).
2. Copy the contents of this zip's `lifeops/` folder over my existing `lifeops/`
   folder. The zip has no `.git`, so my history stays as it is.
3. Delete stale bytecode: `rm -rf backend/app/__pycache__ backend/app/*/__pycache__`
   (`.gitignore` now ignores these).
4. `cp backend/.env.example backend/.env` and `cp frontend/.env.example frontend/.env`.
5. Reinstall dependencies: `pip install -r backend/requirements-dev.txt` and
   `cd frontend && npm ci` (new packages: alembic, bcrypt, PyJWT, httpx,
   react-router).
6. **Existing database:** do the stamp step below *before* starting the API.

### Existing DB: `alembic stamp` (one time)

My current database already has `weight_entries` and `weight_goals`. Those
tables were made by `Base.metadata.create_all`, which is gone now. Alembic is in charge
of the schema from here on. Revision `0001_health_tables` is exactly those two
tables, as the old code created them. So I tell Alembic "this DB is already at 0001"
and then let it create everything else:

```bash
cd backend
alembic stamp 0001_health_tables   # records the version, changes no tables
alembic upgrade head               # creates the Money/Calendar/Invest/Career tables
alembic current                    # -> 0002_lifeops_modules (head)
```

My existing weights and goals are left untouched. This exact flow was tested on
a database created by the original code, both by hand and in
`tests/test_migrations.py`.

A **fresh** database just needs `alembic upgrade head`.

---

## Environment variables

Backend settings are read from the real environment first, then `backend/.env`
(see `app/config.py`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://lifeops:lifeops@localhost:5432/lifeops` | SQLAlchemy URL (used by the API and Alembic) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed frontend origins |
| `APP_TIMEZONE` | `America/New_York` | Sets what "today" means for agenda, bills and the monthly summary |
| `AUTH_ENABLED` | `false` | Turns on JWT login |
| `APP_USERNAME` | `luke` | Login username |
| `APP_PASSWORD_HASH` | – | bcrypt hash (preferred). Generate with `scripts/hash_password.py`. Keep it in single quotes in `.env` |
| `APP_PASSWORD` | – | Plain-text password, local dev only. Used only if there's no hash |
| `JWT_SECRET` | – | Signing key. Required when auth is on |
| `JWT_EXPIRE_MINUTES` | `720` | Token lifetime |
| `TWELVE_DATA_API_KEY` | – | Stock prices (free key at twelvedata.com) |
| `COINGECKO_API_KEY` | – | Crypto prices (free "Demo" key at coingecko.com/en/api) |
| `MARKET_CACHE_TTL_SECONDS` | `60` | How long a price stays cached in memory |
| `MARKET_HTTP_TIMEOUT_SECONDS` | `8` | Timeout for market-data calls |
| `TEST_DATABASE_URL` | `…/lifeops_test` | Tests only. This DB is **dropped and recreated** on each run |

Frontend (build-time, `frontend/.env`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000` | Base URL of the API |

If `AUTH_ENABLED=true` but `JWT_SECRET` or a password is missing, the API
refuses to start. That way it can't run "protected" with an empty secret.

---

## API overview

Full interactive docs are at `/docs`. Every route except `/`, `/healthz`,
`/readyz`, `/auth/*` login/config and `/docs` requires a Bearer token when
`AUTH_ENABLED=true`.

**System & auth**
- `GET /healthz` – liveness (process is up, no DB call)
- `GET /readyz` – readiness (`SELECT 1` against Postgres; returns 503 if the DB is down)
- `GET /auth/config` – `{auth_enabled}` so the frontend knows whether to show login
- `POST /auth/login` – `{username, password}` → `{access_token, token_type, expires_in}`
- `GET /auth/me`

**Health** (unchanged paths)
- `GET/POST /weights`, `PATCH/DELETE /weights/{id}`
- `GET/POST /weight-goals`, `GET /weight-goals/active`, `GET/PATCH/DELETE /weight-goals/{id}`
- `POST /weight-goals/{id}/activate`, `POST /weight-goals/{id}/complete`
- `GET /weight-progress`

**Money** (`/money`)
- CRUD: `/accounts`, `/categories`, `/transactions`, `/budgets`, `/bills`, `/debts`
- `GET /transactions?start_date&end_date&category_id&transaction_type&account_id&limit`
- `POST /budgets/copy` – copy one month's budgets to another month
- Bills have `frequency` (monthly / quarterly / yearly), `due_day`, `autopay`, and a computed `next_due_date`
- `GET /debts/payoff?extra_payment=200&strategy=avalanche|snowball` – months to payoff, total interest, per-debt payoff month, and how much the extra payment saves compared with minimums only
- `GET /summary?year&month&bills_before` – income, spending, net, spending vs budget per category, upcoming bills before a date (default: next 30 days)

**Calendar** (`/calendar`)
- CRUD: `/events`, `/tasks`
- `POST /tasks/{id}/complete` – marks it done. If it recurs (daily/weekly/monthly), the next one is created
- `GET /agenda/today?on=`, `GET /agenda/week?on=` (Mon–Sun), `GET /upcoming?days=7`

**Invest** (`/invest`)
- CRUD: `/holdings` (symbol, asset_type stock|crypto, quantity, avg_cost), `/watchlist`
- `GET /portfolio` – each holding with price + `price_status`, plus market value, cost basis, gain/loss $ and %, and allocation (stock vs crypto)
- `GET /quote/{stock|crypto}/{symbol}`, `GET /watchlist?with_prices=true`
- `price_status` is `ok`, `missing_api_key`, `not_found` or `unavailable`. A missing key or provider outage never causes an error; the price is just `null`

**Career** (`/career`)
- CRUD: `/applications`, `/interviews`, `/contacts`, `/certifications`
- `GET /pipeline` – counts by status, active count, response rate, upcoming interviews

**Dashboard**
- `GET /dashboard` – latest weight + goal progress, this month's spending vs budget + bills due in 14 days, today's agenda, portfolio summary (`status: ok | partial | unavailable`), career pipeline

---

## How the backend works (a tour)

**1. Startup.** `uvicorn app.main:app` imports `main.py`. That file builds the
FastAPI app, adds CORS for the origins in `CORS_ORIGINS`, checks the auth
config is sane, and mounts one router per module. Settings all come from
`config.py`. It loads `backend/.env` with python-dotenv and then reads `os.environ`,
so the same code runs locally (from `.env`) and in a container (from real env vars)
without changes.

**2. A request's path.** Take `GET /money/summary`:
1. FastAPI matches it to a function in `routers/money.py`.
2. Before the function runs, FastAPI resolves its *dependencies*.
   `require_auth` checks the JWT (or does nothing when auth is off), and `get_db`
   opens a SQLAlchemy session that is closed when the request finishes.
3. The router stays thin. It validates input and calls `services/money.py`,
   which does the real work: query transactions for the month, group by category,
   join with budgets, work out which bills fall before the cutoff date.
4. The result is returned as a **Pydantic schema** (`schemas/money.py`), which
   validates the output and turns it into JSON.

That gives three layers, with the same pattern I used for Health:
**models** (database tables), **schemas** (API shapes), **routers** (HTTP), plus
**services** for logic worth testing on its own.

**3. Database and migrations.** Models are SQLAlchemy 2 classes using
`Mapped[...]`. Money is stored as `Numeric(12, 2)` and handled as Python
`Decimal`, so cents never pick up float rounding errors. Alembic owns the schema.
I change a model, run `alembic revision --autogenerate`, review the file, and run
`alembic upgrade head`. The app no longer calls `create_all`, so the
database is never changed behind Alembic's back.

**4. Business rules worth knowing.**
- *Weight goals:* only one active goal at a time. Activating sets `activated_at`, and completing sets `completed_at` (my original rules, unchanged).
- *Bills:* `next_due_date` comes from `due_day` + `frequency`. A due day of 31 becomes the last day of short months.
- *Debt payoff:* a month-by-month simulation. Each month interest is added (APR/12), then every debt gets its minimum and the extra money goes to one target debt. *Avalanche* targets the highest APR (saves the most interest), and *snowball* targets the smallest balance. When a debt is paid off, its minimum "rolls over" to the next one. If the payments can't cover the interest, the endpoint says the plan is not feasible instead of looping forever.
- *Recurring tasks:* completing one creates the next occurrence (+1 day/week/month).

**5. Market data.** `services/market_data.py` wraps two providers behind one
`get_price(asset_type, symbol)` call. Stocks go to Twelve Data and crypto goes to
CoinGecko. CoinGecko wants coin ids, so `BTC` → `bitcoin` comes from a small table,
with the `/search` endpoint as a fallback. Calls use `httpx` with a timeout, and results
sit in an in-memory TTL cache (60s) to stay inside the free tiers. Every
failure is turned into a `price_status` instead of an exception, so the portfolio
and dashboard still load without keys or internet. The service is a FastAPI
dependency, so tests swap in a fake one and never hit the network.

**6. Auth.** It's single-user, so there's no users table. With `AUTH_ENABLED=true`,
`POST /auth/login` checks the username against `APP_USERNAME` and the password
against the bcrypt hash, then returns a signed JWT (HS256, `JWT_SECRET`). Every
protected router has `Depends(require_auth)`, which checks the
`Authorization: Bearer …` header. The frontend stores the token and attaches
it to every request. On a 401 it sends you back to the login page.

**7. Health checks.** `/healthz` only says "the process is alive". `/readyz`
says "I can reach the database". An orchestrator should restart on the first and
stop routing traffic on the second.

**8. Tests.** `pytest` spins up a throwaway `lifeops_test` database, runs the
real Alembic migrations, and drives the API through FastAPI's `TestClient`.
Tables are truncated between tests. The tests cover CRUD for every module, the goal rules,
payoff math, budget summaries, portfolio math with mocked prices, auth on/off, and
the migration/stamp path. The DB user needs permission to create databases
(the compose `lifeops` user has it).

---

## DevOps work left for me

The application is done. These are my next hands-on milestones to ship it.

### 1. Dockerfiles
- **API image:** Python 3.14 slim, `pip install -r requirements.txt`, run as a
  non-root user, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  Migrations (`alembic upgrade head`) run as a separate one-off step or task,
  not on every container start.
- **Frontend image:** multi-stage. `npm ci && npm run build` with
  `VITE_API_URL` passed as a **build arg** (Vite bakes it in at build time), then
  serve `dist/` from nginx with an SPA fallback (`try_files $uri /index.html`).
- `.dockerignore` files for `.venv`, `node_modules`, `.env`, `dist`, caches.

### 2. Full docker-compose
- Add `api` and `frontend` services next to `postgres`. `api` should use
  `depends_on: postgres: condition: service_healthy` (the healthcheck is
  already there) and a healthcheck on `/healthz`.
- `DATABASE_URL` must use the service name (`@postgres:5432`), and
  `CORS_ORIGINS` must include the frontend's URL.
- Watch out: compose treats `$` in values as variable interpolation. A bcrypt
  `APP_PASSWORD_HASH` must be written with `$$`, or put in an `env_file`.

### 3. GitHub Actions CI
- **Backend job:** `postgres:17` service container, Python 3.14,
  `pip install -r requirements-dev.txt`, `ruff check .`, then `pytest` with
  `TEST_DATABASE_URL` pointing at the service.
- **Frontend job:** Node 20+, `npm ci`, `npm run lint`, `npm run build`.
- Then build images and push to **ECR** (OIDC role, no long-lived keys), tagged
  with the git SHA.

### 4. Terraform on AWS
- **VPC:** public subnets for the ALB, private subnets for ECS + RDS.
- **ECS Fargate:** API service behind an ALB. Target group health check
  `GET /healthz`. Optionally a readiness check against `/readyz`. Add a one-off task
  definition for `alembic upgrade head`.
- **RDS PostgreSQL 17** in private subnets. Its security group should allow only the ECS tasks.
- **S3 + CloudFront** for the built frontend (SPA: 403/404 → `/index.html`).
  Build with `VITE_API_URL=https://api.<domain>`.
- **Secrets Manager:** `DATABASE_URL`, `JWT_SECRET`, `APP_PASSWORD_HASH`,
  `TWELVE_DATA_API_KEY`, `COINGECKO_API_KEY`, injected into the task definition
  as `secrets`.
- **Plain task env vars:** `AUTH_ENABLED=true` (keep this on anywhere public),
  `APP_USERNAME`, `CORS_ORIGINS=https://<cloudfront domain>`, `APP_TIMEZONE`,
  `JWT_EXPIRE_MINUTES`, `MARKET_CACHE_TTL_SECONDS`, `MARKET_HTTP_TIMEOUT_SECONDS`.
- **CloudWatch:** log group for the API (uvicorn logs to stdout), alarms on
  ALB 5xx, unhealthy targets and RDS CPU/storage.

Note: the price cache is in-memory and per-process. With more than one API task, each
keeps its own cache. That's fine at this scale. Redis/ElastiCache would be the
upgrade if it ever matters.
