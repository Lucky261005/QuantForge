# QuantForge — Institutional Quantitative Research Platform for Indian Markets

## Architecture &amp; Design Decisions

## 1. Scope

QuantForge is a **research platform for NSE/BSE equities and indices**, not an
execution/OMS system: it produces and evaluates trading signals over historical data. That
framing drives every tradeoff below — several "enterprise" patterns (event bus, broker/fill
simulation, multi-store OLAP) are deliberately **not** built, because they exist to serve
consumers this system doesn't have. Building them unwired would be decorative complexity,
which is worse than not having them.

The platform was repositioned from a generic US-market MVP to an India-first one: the same
architecture (registries, repository/service layers, vectorized engine) now carries Indian
domain content — NSE/BSE symbols and sector taxonomy, NIFTY/BANKNIFTY/SENSEX benchmarks, an
Indian equity transaction-cost model (STT/exchange charges/SEBI charges/stamp duty/GST), and
broker-specific market-data providers. This was a content/domain change, not a rebuild — see
§7 for the genuinely new subsystems (intraday timeframes, F&O/currency/commodities, live
corporate actions) that this repositioning deliberately did **not** attempt to fake.

**Implemented, real and tested:**
- Auth: JWT access + refresh (rotation + server-side revocation via a persisted `jti`), bcrypt
  hashing, RBAC (user/admin), protected routes, mock email verification, forgot-password flow,
  and an opt-in httpOnly refresh-token cookie (`AUTH_COOKIE_ENABLED`) alongside the default
  bearer-token flow — off by default, fully backward compatible when off
- Market data: pluggable `MarketDataProvider` interface — `YahooFinanceProvider` (auto-
  resolves NSE/BSE symbols to `.NS`/`.BO`) and `CSVProvider` fully wired; `NSEOfficialProvider`
  (public NSE JSON API, session-cookie warm-up), `KiteConnectProvider` (Zerodha),
  `UpstoxProvider`, `AngelOneProvider` (SmartAPI), `AlphaVantageProvider`/`PolygonProvider`
  all implement the same interface and activate when their credentials are set (documented,
  API-shape-accurate stubs, not fakes — see §7 for what a full broker integration still needs)
- Deduplicated, cached OHLCV storage (unique on `asset_id, date`, Redis-cached reads), with
  `sector`/`industry`/`market_cap_cr` metadata on every asset, plus a bulk `IN (...)`-query
  path (`get_range_for_assets`) for universe-wide aggregates like market breadth
- **17 technical indicators**: SMA, EMA, MACD, RSI, Bollinger Bands, ATR, VWAP, Stochastic,
  ADX, ROC, SuperTrend, Williams %R, CCI, Aroon, Parabolic SAR, OBV, MFI — pure functions in
  an `IndicatorRegistry`
- Vectorized backtest engine: commission, slippage, position sizing, stop-loss/take-profit,
  multi-asset portfolios with optional periodic rebalancing (monthly/quarterly, additive —
  `run_multi_asset_backtest_with_rebalancing` delegates to the original unmodified function
  when rebalancing is off), and an **Indian equity charge model**
  (`app/backtesting/charges.py`) — STT/exchange transaction charges/SEBI turnover fee/stamp
  duty/GST computed from regulator-set rates, asymmetric between the buy and sell leg,
  selectable per backtest alongside the original flat commission/slippage model
- **21 built-in strategies** (Golden/Death Cross, EMA Crossover, RSI Reversal, MACD, Bollinger
  Breakout, SuperTrend, ADX Trend, Momentum, Swing Breakout/Donchian, VWAP Intraday Trend,
  Moving Average Ribbon, Opening Range Breakout, Williams %R Reversal, CCI Trend, Parabolic SAR
  Trend, OBV Trend Confirmation, Aroon Trend, MFI Reversal, Stochastic Reversal, Bollinger
  Z-Score Reversion, Buy & Hold) behind a `StrategyRegistry` + documented custom-strategy
  plugin API
- Full analytics: Sharpe/Sortino/Calmar, max drawdown, win rate, profit factor, expectancy,
  alpha/beta, volatility, monthly-returns heatmap, **VaR, CVaR, Ulcer Index, Omega ratio,
  max consecutive losses, recovery time**, a **configurable annualized risk-free rate**, and
  **block-bootstrap 95% confidence intervals on Sharpe and CAGR** (`compute_bootstrap_
  confidence_intervals`) — a point estimate alone overstates the statistical confidence a
  few hundred daily returns can support
- **Transaction-cost sensitivity analysis** (`GET /backtests/{id}/cost-sensitivity`) — reruns
  a completed backtest's exact signals at 0×/0.5×/1×/1.5×/2× its cost assumptions
- **Walk-forward validation** (`GET /backtests/{id}/walk-forward`) — reruns the same fixed
  strategy parameters across N rolling out-of-sample windows to check consistency across
  regimes (deliberately *validation*, not full walk-forward *optimization* with per-window
  parameter re-search — see §7)
- **Market breadth** (`GET /assets/breadth`): advance/decline and 52-week high/low counts
  across every stored equity, computed from OHLCV already on file
- **Portfolio optimizer** service: equal-weight, mean-variance, risk parity, max-Sharpe,
  min-volatility (`scipy.optimize`)
- **Experiment tracking** fields on every backtest: strategy version hash, dataset date
  range, runtime, parameter snapshot
- Async execution via Celery + Redis; **per-resource API** — `/backtests/{id}/status`,
  `/metrics`, `/equity`, `/trades`, `/cost-sensitivity`, `/walk-forward` rather than one fat
  payload; rate-limited (backtest creation and every write endpoint, not just auth/downloads)
- A `GET /health/ready` readiness probe (checks DB + Redis independently of the liveness
  `/health` endpoint) and a startup guard that refuses to boot with the default `SECRET_KEY`
  when `ENVIRONMENT=production`
- `selectinload`/`joinedload` eager-loading on every list endpoint that serializes a
  relationship (watchlists, backtest→strategy in comparisons) — verified by a query-count
  regression test, not just checked by eye
- Watchlists (including sector watchlists — Banking, IT, Auto, Pharma, FMCG, Energy, PSU),
  research notes, portfolio/transactions, and an audit log now covering backtest/strategy/
  portfolio mutations in addition to auth events
- Next.js 14 frontend: landing, auth, research dashboard (market overview, market breadth,
  top gainers/losers, a sector heatmap), strategy builder, backtest results (Plotly
  candlestick/equity/drawdown/monthly-heatmap/trade-distribution), analytics/comparison
  (equity overlay, ranking, correlation matrix, risk-vs-return scatter), watchlist, settings —
  dark/light theme, ₹/INR formatting throughout, and a baseline accessibility pass (skip link,
  labeled icon-only controls, an accessible command-palette dialog, app-wide
  `prefers-reduced-motion` support)
- Dockerized (Postgres, Redis, backend, Celery worker, frontend, Nginx), GitHub Actions CI,
  pytest (unit + API) — **124 tests, 89% coverage**, Alembic migrations

**Explicitly out of scope, with reasoning (see §7 for how each would slot in):**
- *Event-driven pub/sub domain events* — a backtest result today has exactly one consumer
  (the UI, via polling). A message bus with no second subscriber is unused machinery.
- *Broker/fill simulation, order queue, execution engine* — these earn their complexity in
  an intraday/live-trading OMS. For daily-bar research backtests they'd be an unwired
  `FillEngine` that just multiplies price × qty — worse than not having it.
- *DuckDB as a third data store* — no OLAP-scale workload exists yet that Postgres can't
  serve; adding it now is an ops cost with no payoff.
- *Live broker wiring (Kite Connect/Upstox/Angel One/Alpha Vantage/Polygon)* — no broker
  accounts or API keys available; each provider is a real, API-shape-accurate implementation
  behind the same interface as Yahoo Finance, and activates once its credentials are set.
  Kite/Upstox/Angel One additionally need their instrument-master lookup (symbol →
  instrument token) wired for anything beyond large-cap NSE equity — see §7.
- *Intraday multi-timeframe backtesting (5m/15m/30m/1h)* — the engine and all strategies
  operate on whatever bar frequency they're given, and the Opening Range Breakout strategy is
  written session-aware for this reason, but no intraday data provider or UI timeframe picker
  exists yet. Faking intraday behavior on daily bars would misrepresent VWAP-Intraday/ORB
  results, so this is left as an honest gap rather than simulated — see §7.
- *Futures, Options, Currency, Commodities* — the `Asset`/`AssetType` model and provider
  interface both generalize to these (an options chain is still OHLCV-shaped data with extra
  contract metadata), but no options-pricing/margin/expiry logic exists — see §7.
- *Corporate actions / earnings calendar feed* — the dashboard's "Upcoming Earnings" and
  "Corporate Actions" widgets from the original ask were deliberately not stubbed with fake
  data; this needs a real ingestion pipeline (NSE corporate-announcements API), not a
  cosmetic placeholder — see §7.
- *ML model zoo (XGBoost/LightGBM/LSTM), live WebSocket ticks, PDF/Excel export, market
  scanner, trade journal, pairs trading* — roadmap items, see §7.

## 2. Why these choices

- **FastAPI + Pydantic v2** — async I/O for data downloads, automatic OpenAPI docs, typing
  that gives the TS frontend a real contract via generated types.
- **SQLAlchemy 2.0 (typed) + Alembic** — the repository pattern needs an explicit
  unit-of-work ORM; Alembic gives reviewable, versioned schema history — no `create_all`
  in production.
- **SQLite for dev / Postgres for prod** — identical SQLAlchemy models across both;
  SQLite keeps local dev and `docker compose up` frictionless.
- **Repository + Service layer** — routers never touch the ORM. Repository = persistence
  only; Service = business rules ("a backtest must have `end_date > start_date`", "a
  strategy's parameter values must satisfy its JSON schema"). This is what makes the
  backtest engine unit-testable with zero database dependency.
- **Celery + Redis** — a multi-year daily backtest can take a few seconds; doing it
  in-request blocks the event loop and risks gateway timeouts under load. Redis doubles as
  the Celery broker and the market-data/indicator cache.
- **Vectorized backtest engine** — the engine operates on aligned signal/return vectors
  (pandas/numpy) and only iterates row-by-row for trade-level bookkeeping (entries/exits/
  stop checks). An event-by-event Python loop over years of bars is slower and no more
  correct for daily-bar research — this is the standard tradeoff, and iterating for tick
  data would be a different product.
- **Registries over hardcoded dispatch** — `StrategyRegistry` and `IndicatorRegistry` are
  decorator-based (`@register_strategy("rsi_mean_reversion")`); adding a strategy means
  adding one file, not editing a switch statement. This is the real mechanism behind the
  "Custom Strategy API" claim.
- **Next.js 14 App Router + TanStack Query + Zustand** — server components for the
  marketing/landing page (fast first paint, SEO), client components + TanStack Query for
  authenticated data (caching, retries, background refetch), Zustand only for small global
  UI/auth state.
- **shadcn/ui over a component library** — primitives are copied into the repo so the
  glassmorphism/dark-mode design system can be fully owned, not fought against.

## 3. Folder structure

```
QuantForge/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app factory, middleware, routers
│   │   ├── core/                       # config, security, logging, celery app, cache
│   │   ├── db/                         # engine/session, declarative base
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   ├── schemas/                    # Pydantic v2 request/response models
│   │   ├── repositories/               # data access, one per aggregate
│   │   ├── services/                   # business logic, orchestration
│   │   ├── market_data/                # MarketDataProvider interface + implementations
│   │   ├── indicators/                 # pure functions + IndicatorRegistry
│   │   ├── strategies/                 # Strategy ABC, StrategyRegistry, built-ins
│   │   ├── backtesting/                # engine, metrics, optimizer
│   │   ├── tasks/                      # Celery tasks (async backtests)
│   │   ├── api/v1/endpoints/           # routers (thin — call services only)
│   │   └── utils/
│   ├── alembic/                        # migrations
│   ├── tests/{unit,integration,api}
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                            # Next.js 14 + TS + Tailwind + shadcn/ui
├── docker/                              # nginx.conf
├── docs/                                # architecture, ER diagram, API notes, deployment
├── scripts/                             # dev bootstrap scripts
├── .github/workflows/                   # CI
└── docker-compose.yml
```

## 4. Database schema (overview — full DDL in `docs/ER_DIAGRAM.md`)

```
users (1)──(N) refresh_tokens
users (1)──(N) strategies (1)──(N) backtests (1)──(1) backtest_results
backtests (1)──(N) trades
assets (1)──(N) market_data
assets (1)──(N) trades / watchlist_items / portfolio_holdings
users (1)──(N) watchlists (1)──(N) watchlist_items
users (1)──(N) research_notes
users (1)──(1) portfolios (1)──(N) portfolio_holdings / transactions
users (1)──(N) audit_logs
```

`backtests` carries experiment-tracking columns: `strategy_version_hash`,
`data_start`/`data_end`, `runtime_seconds`, `parameters_snapshot` (JSON), so results remain
reproducible even after a strategy's parameters change later.

## 5. API design

- Versioned under `/api/v1`, documented at `/docs` (Swagger) and `/redoc`.
- Pagination: `?page=&page_size=` → `{items, total, page, page_size, pages}`.
- Filtering/sorting: `?sort=-created_at&symbol=RELIANCE`, parsed by one shared dependency.
- Rate limiting: Redis-backed, applied to auth + data-download endpoints.
- Errors: RFC7807-style problem-detail JSON via one central exception handler.
- Backtests expose sub-resources instead of one payload: `GET /backtests/{id}/status`,
  `/metrics`, `/equity`, `/trades` — lets the frontend cache and load each independently.

## 6. UI structure

- **Landing** — dark hero with gradient mesh, animated equity-curve sparkline, feature
  grid, CTA → register. Framer Motion scroll reveals.
- **Research Dashboard** — left nav rail, ⌘K command palette, KPI cards (portfolio value,
  today's P&L, Sharpe, open positions), a market overview strip (NIFTY 50/BANK NIFTY/SENSEX),
  top gainers/losers and sector performance (derived client-side from stored OHLCV — see §7
  for a live quote feed), recent backtests table, watchlist ticker strip.
- **Strategy Builder** — pick a strategy type → dynamic parameter form generated from the
  backend's JSON schema for that strategy → asset/date-range picker → risk params → Run.
- **Backtest Results** — candlestick chart with trade markers, equity + drawdown subplot,
  metrics grid, monthly-returns heatmap, trade blotter.
- **Analytics** — multi-backtest comparison (overlaid equity curves, ranking table,
  risk/return scatter, correlation matrix, rolling Sharpe).
- **Watchlist / Settings / Profile / Login / Register** — consistent glass/card styling,
  skeleton loaders on fetch.

## 7. Extension seams (roadmap items, not built now)

- **ML models** — `app/ml/` mirrors `strategies/`: a `FeaturePipeline` + `ModelRegistry`
  contract; add `RandomForestModel`/`XGBoostModel`/`LightGBMModel` behind one
  `BasePredictor` interface, wire a `/api/v1/ml` router the same way `backtests` is wired.
- **Live prices** — the market-data service already isolates "get latest price" behind the
  provider interface, so it can move from polling to a `/ws/prices/{symbol}` push loop
  without touching callers.
- **Execution/OMS layer** — if this ever needs to place real orders, `backtesting/engine.py`
  is the seam: its trade-generation step would emit `OrderIntent` objects consumed by a new
  `execution/` package (order queue → broker adapter → fill engine), instead of directly
  producing `Trade` rows as it does today.
- **Domain events** — if a second consumer of backtest completion ever exists (e.g. a
  notification service), promote the current direct `service → repository` call in
  `tasks/backtest_tasks.py` to publish a `BacktestCompleted` event on Redis pub/sub.
- **Exports** — analytics endpoints already return fully-structured JSON; a `reporting/`
  package renders PDF/XLSX from that same service-layer output, no metric-logic duplication.
- **Intraday multi-timeframe backtesting** — `MarketData` and the engine are timeframe-
  agnostic (they operate on whatever bars they're given), so the real work is: (1) a
  `timeframe` column on `MarketData`/`Asset` requests instead of assuming one daily bar per
  day, (2) an intraday-capable provider (Kite/Upstox/Angel One all expose 1m–1h candles,
  unlike the daily-only Yahoo/NSE-official paths here), (3) a timeframe picker in the
  Strategy Builder UI. `OpeningRangeBreakoutStrategy` and `VWAPTrendStrategy` are already
  written session-aware for exactly this reason — they just have no intraday data to run on
  yet.
- **Instrument-master resolution for Kite/Upstox/Angel One** — `KiteConnectProvider`
  resolves `tradingsymbol → instrument_token` by fetching Kite's full instrument CSV per
  call; Upstox/Angel One currently assume a direct `NSE_EQ|{symbol}` convention or a
  caller-supplied token. A production integration would cache each broker's instrument
  master (refreshed daily) in its own table and resolve against that instead.
- **Walk-forward *optimization*** (as distinct from the walk-forward *validation* already
  built) — re-searching strategy parameters per rolling window instead of holding them
  fixed. The seam is `BacktestService.run_walk_forward_validation`: swap the single
  `self._config_for(backtest)` call for a per-window parameter search (grid or Bayesian)
  over `strategy.parameters`' declared `ParamSpec` ranges, which already exist for every
  built-in strategy and are what the Strategy Builder's dynamic forms already read.
- **Rolling Sharpe/volatility as a time series, and a trade calendar (daily-P&L calendar
  heatmap)** — both are computable from data the backend already returns (`daily_returns`
  on `BacktestResult`, and the trade blotter's `entry_date`/`pnl`); the remaining work is
  frontend-only (a new Plotly chart component per view), not a new endpoint.
- **Live paper trading** — a distinct subsystem from the backtest engine (order simulation
  against live/delayed quotes, position tracking, a fills feed), not an extension of it.
  The natural seam is the same one described above for a real Execution/OMS layer: a
  `paper_trading/` package consuming `OrderIntent` objects against a simulated broker
  instead of the historical engine's vectorized fills.
- **Futures, Options, Currency, Commodities** — `AssetType` already has room to grow past
  `EQUITY`/`ETF`/`INDEX`; an options chain needs a new `OptionContract` model (strike,
  expiry, option type) referencing the existing `Asset` as its underlier, plus
  Black-Scholes/margin logic in a new `app/derivatives/` package — deliberately not
  approximated by reusing the equity backtest engine, which has no concept of expiry or
  premium decay.
- **Corporate actions / earnings calendar** — a `CorporateAction` model (symbol, type —
  dividend/split/bonus — ex-date, ratio) fed by NSE's public corporate-announcements API,
  surfaced on the dashboard and consulted by the backtest engine for split/dividend-adjusted
  historical prices (today's `adj_close` field is populated by the data provider, not
  computed from actions QuantForge tracks itself).
