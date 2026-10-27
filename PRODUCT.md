# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: recruiters, interviewers and engineers evaluating the author's work, exploring through the
seeded demo account (`demo@quantforge.io`). The product is framed as if for retail quants and small
research desks in India who think in rules; that framing must stay credible to a domain expert.

## Product Purpose
A research and backtesting platform for NSE/BSE equities and indices. It turns a rule into a
verdict: load bars, compute indicators, run a strategy, read risk-adjusted results. It never places
orders and is not connected to any broker. Success: an evaluator understands what it does within
seconds, opens the demo desk, and finds a finished, credible tool.

## Positioning
Undecided by the user. Defensible candidates from the code: results net of the Indian statutory
charge model (STT, exchange charges, SEBI fee, stamp duty, GST, `backend/app/backtesting/charges.py`);
statistical rigour (walk-forward, block-bootstrap CIs); breadth (17 indicators, 21 strategies,
optimizer, comparison).

## Capabilities and Constraints
- FastAPI backend, Next.js 14 App Router frontend with Tailwind and shadcn-style tokens.
- Market data: Yahoo Finance with NSE/BSE symbol resolution, CSV; Kite, Upstox, SmartAPI,
  Alpha Vantage, Polygon behind one interface.
- 17 indicators, 21 strategies, vectorised backtest engine, risk suite, walk-forward,
  portfolio optimizer (5 methods), market breadth, Celery async backtests, JWT auth with RBAC.
- Research and education only; not investment advice.

## Evidence on Hand
- Demo data via `scripts/seed_demo_data.py`: 20 NSE large caps, 6 index series, watchlists,
  completed backtests.
- 124 backend tests, 89% coverage.
- No customers, testimonials, performance track record or press. Never fabricate them; no
  invented equity curves or returns on public pages.

## Product Principles
- Honest numbers only: every figure shown is computed by the product or is a product fact.
- Indian market native: ₹/INR, lakh/crore grouping, IST, NSE/BSE terminology.
- Orientation first: an evaluator should reach the demo desk in one click.
- Research, never execution: nothing suggests live trading.
