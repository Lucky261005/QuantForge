# QuantForge

QuantForge is a backtesting and research platform for Indian equities (NSE/BSE). You load daily
price data, pick or configure a rule-based strategy, and get a backtest with Indian transaction
charges applied to every trade, risk metrics with confidence intervals, and robustness checks.

It is a student portfolio project, built as a working full-stack application. It is a research
tool, not a trading system: it has no broker execution, no live prices, and makes no claim that
any strategy is profitable. The demo data it ships with is synthetic and labelled as such.

## What problem it solves

Most hobby backtesters ignore what trading in India actually costs (STT, stamp duty, exchange and
SEBI fees, GST), fill stop-losses at prices the market never offered, and report a single Sharpe
ratio with no sense of how uncertain it is. QuantForge models those costs per trade, fills stops
and targets realistically when prices gap through them, and reports bootstrap confidence intervals,
walk-forward results and cost sensitivity next to the headline numbers.

**Intended users:** students and individual researchers exploring systematic strategies on Indian
markets who want results they can reason about.

## Features

- **21 built-in strategies** (moving-average and EMA crossovers, MACD, RSI, Bollinger, Donchian,
  SuperTrend, buy-and-hold and more) behind a plugin registry, built on **17 indicators**.
- **Backtest engine:** signals act one bar later; stops and targets fill at the trigger level, or
  at the open when the bar gaps through it; long and short positions; multi-asset portfolios with
  periodic rebalancing; slippage and position sizing.
- **Indian equity charge model:** STT, exchange transaction charges, SEBI turnover fee, stamp duty
  and GST for delivery and intraday trades, or a simple flat commission.
- **Risk metrics:** CAGR, volatility, Sharpe, Sortino, Calmar, Omega, max drawdown, Ulcer Index,
  VaR/CVaR, alpha/beta against a benchmark, and block-bootstrap 95% confidence intervals for
  Sharpe and CAGR.
- **Robustness tools:** walk-forward validation over rolling windows, transaction-cost
  sensitivity, side-by-side comparison of backtests with a correlation matrix, and a portfolio
  optimizer (5 allocation methods via SciPy).
- **Market data:** CSV upload (verified path) and Yahoo Finance with NSE/BSE symbol resolution.
  Adapters for Kite Connect, Upstox, Angel One, NSE, Alpha Vantage and Polygon are implemented
  but untested against the live APIs.
- **Accounts and security:** JWT access and refresh tokens with rotation and revocation, roles,
  per-user ownership checks on every resource, rate-limited login, single-use password-reset
  tokens, and security headers.
- **Frontend:** dashboard, strategy builder, backtest results with Plotly charts (equity,
  drawdown, monthly returns, trades), comparison, optimizer, paper portfolio, watchlists and
  research notes; INR formatting, keyboard command palette, accessibility pass.
- **Async execution:** backtests run on a Celery worker when Redis is available, and in-process
  when it isn't.

## Architecture

```
 Browser (Next.js 14, TanStack Query, Plotly)
        │  REST /api/v1, JWT
        ▼
 Nginx ──► FastAPI ── endpoints → services → repositories → SQLAlchemy models
                │            │
                │            ├── backtest engine (signals, fills, charges, metrics)
                │            ├── market data providers (CSV, Yahoo, broker adapters)
                │            └── Redis cache (in-memory fallback)
                ▼
        PostgreSQL (Docker) / SQLite (local)
                ▲
                │
        Celery worker ◄── Redis broker (optional; falls back to in-process runs)
```

A backtest request saves a pending backtest, dispatches it to the worker, and the engine loads
stored bars, lags the strategy's signals by one bar, simulates trades with slippage and charges,
and stores metrics, trades and the equity curve. The frontend polls until it completes. More in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quickstart (Docker)

Requires Docker with Compose.

```bash
cp .env.example .env
# Set a random SECRET_KEY in .env, e.g. from: openssl rand -hex 32
# (the example sets ENVIRONMENT=production, and the API refuses to start with the example key)
docker compose up --build
```

Open http://localhost. This starts PostgreSQL, Redis, the API (migrations run on start), a Celery
worker, the frontend and Nginx. Compose also publishes Postgres, Redis, the API (8000) and the
frontend (3000) on host ports for convenience; remove those mappings anywhere but your own machine.

To load the demo account and synthetic demo data into the running stack:

```bash
cd backend && pip install -r requirements.txt   # the seed script uses httpx
QUANTFORGE_API_URL=http://localhost/api/v1 python ../scripts/seed_demo_data.py
```

Then sign in as `demo@quantforge.io` / `DemoPass123` (a local demo account only).

## Local development (without Docker)

Requires Python 3.12+ and Node 20+. Redis is optional.

```bash
# Backend (http://localhost:8000/api/v1, docs at /api/v1/docs)
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Demo data (with the backend running)
python ../scripts/seed_demo_data.py

# Frontend (http://localhost:3000)
cd ../frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

Locally the backend uses SQLite (`backend/quantforge.db`) and development settings. If the
frontend runs on a port other than 3000, add it to `CORS_ORIGINS`. Password-reset emails are
written to `backend/dev_outbox/` instead of being sent.

## Tests

| Suite | Command | Result |
|---|---|---|
| Backend (pytest) | `cd backend && pytest` | 191 passed, including hand-computed financial cases |
| Lint and format | `ruff check app/` and `black --check app/` | clean |
| Frontend | `npm run lint`, `npm run type-check`, `npm test`, `npm run build` | clean, 6 unit tests passed |
| End-to-end (Playwright) | `E2E_BASE_URL=http://localhost:3000 npm run test:e2e` against a seeded stack | 4 passed |
| CI | GitHub Actions: backend, frontend and Docker image builds | passing |

The full Docker stack was also verified from a clean start: migrations on an empty PostgreSQL,
health checks, sign-up, sign-in, CSV upload and CORS through Nginx, demo backtests completed by
the Celery worker, and the Playwright tests against it.

## Project structure

```
backend/     FastAPI app, backtest engine, strategies, Alembic migrations, tests
frontend/    Next.js 14 app (App Router), Vitest and Playwright tests
docker/      Nginx config
docs/        architecture, ER diagram, API notes, deployment notes
scripts/     demo data seeding
```

## Documentation

- [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md): detailed technical write-up
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): design decisions and scope
- [docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md): database schema
- [docs/API.md](docs/API.md): API overview and auth flow
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): deployment notes

## Tech stack

Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pandas, NumPy, SciPy, Celery, Redis,
PostgreSQL / SQLite · Next.js 14, TypeScript, Tailwind CSS, TanStack Query, Zustand, Plotly ·
pytest, Vitest, Playwright · Docker Compose, Nginx, GitHub Actions

## Limitations

- **Synthetic demo data.** The seeded prices are random walks; results on them are illustrative.
- **Daily bars only.** No intraday backtesting, derivatives, corporate actions or live prices.
- **Simplified execution.** Shorts carry no borrow fees or margin. Walk-forward re-tests fixed
  parameters; it does not re-optimize them per window.
- **Unverified data providers.** Only CSV upload and the Yahoo adapter's code path are verified;
  Yahoo itself may rate-limit some networks.
- **Charge rates** reflect published NSE/SEBI rates at the time of writing and change by
  regulation.
- **Not production-ready.** Behind Nginx, rate limits are shared across clients; there is no
  Content-Security-Policy; and Starlette (via FastAPI) and Next.js 14 have published advisories
  that need upgrades. It has not been deployed publicly.
