# Database ER Diagram

Generated from the SQLAlchemy models in `backend/app/models/`. The initial Alembic migration
(`backend/alembic/versions/b5ae66c763f8_initial_schema.py`) creates exactly this schema — verified
to apply cleanly to a fresh database with zero drift (`alembic check`).

```mermaid
erDiagram
    USERS ||--o{ REFRESH_TOKENS : issues
    USERS ||--o{ STRATEGIES : owns
    USERS ||--o{ BACKTESTS : owns
    USERS ||--o{ WATCHLISTS : owns
    USERS ||--o{ RESEARCH_NOTES : writes
    USERS ||--o| PORTFOLIOS : has
    USERS ||--o{ AUDIT_LOGS : generates

    STRATEGIES ||--o{ BACKTESTS : "backtested as"
    BACKTESTS ||--o| BACKTEST_RESULTS : produces
    BACKTESTS ||--o{ TRADES : generates

    ASSETS ||--o{ MARKET_DATA : "has bars"
    ASSETS ||--o{ TRADES : "traded in"
    ASSETS ||--o{ WATCHLIST_ITEMS : "listed in"
    ASSETS ||--o{ PORTFOLIO_HOLDINGS : "held as"
    ASSETS ||--o{ TRANSACTIONS : "transacted as"

    WATCHLISTS ||--o{ WATCHLIST_ITEMS : contains
    PORTFOLIOS ||--o{ PORTFOLIO_HOLDINGS : contains
    PORTFOLIOS ||--o{ TRANSACTIONS : records

    USERS {
        int id PK
        string email UK
        string username UK
        string hashed_password
        string full_name
        enum role "user | admin"
        bool is_active
        bool is_verified
        datetime created_at
    }

    REFRESH_TOKENS {
        int id PK
        int user_id FK
        string jti UK
        datetime expires_at
        bool revoked
    }

    ASSETS {
        int id PK
        string symbol UK
        string name
        enum asset_type
        string exchange
        string currency "default INR"
        string sector "nullable"
        string industry "nullable"
        float market_cap_cr "nullable, INR crore"
    }

    MARKET_DATA {
        int id PK
        int asset_id FK
        date date
        float open
        float high
        float low
        float close
        float adj_close
        float volume
        enum source "yahoo_finance | nse_official | kite_connect | upstox | angel_one | alpha_vantage | polygon | csv_upload"
    }

    STRATEGIES {
        int id PK
        int owner_id FK
        string name
        string strategy_type "registry key, e.g. ma_cross"
        json parameters
        bool is_public
    }

    BACKTESTS {
        int id PK
        int owner_id FK
        int strategy_id FK
        json symbols
        date start_date
        date end_date
        float initial_capital
        float commission_pct
        float slippage_pct
        float position_size_pct
        float stop_loss_pct "nullable"
        float take_profit_pct "nullable"
        string benchmark_symbol "default NIFTY50"
        enum charge_model "flat | indian_equity_delivery | indian_equity_intraday"
        float brokerage_pct
        float risk_free_rate_annual "used in Sharpe/Sortino"
        string rebalance_frequency "none | monthly | quarterly"
        enum status "pending | running | completed | failed"
        string strategy_version_hash "experiment tracking"
        json parameters_snapshot "experiment tracking"
        float runtime_seconds
        string error_message
    }

    BACKTEST_RESULTS {
        int id PK
        int backtest_id FK "unique"
        float total_return_pct
        float cagr_pct
        float sharpe_ratio
        float sortino_ratio
        float calmar_ratio
        float omega_ratio
        float max_drawdown_pct
        float ulcer_index
        float var_95_pct
        float cvar_95_pct
        int max_consecutive_losses
        int num_trades
        float win_rate_pct
        float profit_factor
        float expectancy
        float alpha
        float beta
        float sharpe_ratio_ci_low "block-bootstrap 95% CI"
        float sharpe_ratio_ci_high
        float cagr_pct_ci_low
        float cagr_pct_ci_high
        json equity_curve
        json drawdown_curve
        json monthly_returns
        json daily_returns
    }

    TRADES {
        int id PK
        int backtest_id FK
        int asset_id FK
        enum side "long | short"
        date entry_date
        float entry_price
        date exit_date
        float exit_price
        float quantity
        float pnl
        float pnl_pct
        enum exit_reason "signal | stop_loss | take_profit | end_of_backtest"
    }

    WATCHLISTS {
        int id PK
        int owner_id FK
        string name
    }

    WATCHLIST_ITEMS {
        int id PK
        int watchlist_id FK
        int asset_id FK
        datetime added_at
    }

    RESEARCH_NOTES {
        int id PK
        int owner_id FK
        string title
        text content
        json tags
        int related_strategy_id FK "nullable"
        int related_backtest_id FK "nullable"
    }

    PORTFOLIOS {
        int id PK
        int owner_id FK "unique"
        string name
        float cash_balance
    }

    PORTFOLIO_HOLDINGS {
        int id PK
        int portfolio_id FK
        int asset_id FK
        float quantity
        float avg_price
    }

    TRANSACTIONS {
        int id PK
        int portfolio_id FK
        int asset_id FK "nullable"
        enum type "buy | sell | deposit | withdraw"
        float quantity
        float price
        float amount
        datetime timestamp
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK "nullable"
        string action
        string resource_type
        int resource_id
        json details
        string ip_address
        datetime timestamp
    }
```

## Notable design choices

- `market_data` is unique on `(asset_id, date)` — the enforcement mechanism behind "prevent
  duplicate downloads," combined with an app-level check (`MarketDataService._is_range_fully_cached`)
  that skips the external API call entirely when the requested range is already stored.
- `backtests` carries `strategy_version_hash` and `parameters_snapshot` rather than only a foreign
  key to `strategies` — a strategy's parameters can be edited later without invalidating the
  reproducibility of past results (experiment tracking, see `docs/ARCHITECTURE.md`).
- `backtest_results` is 1:1 with `backtests` (not embedded) so the heavy JSON payloads (equity
  curve, drawdown curve, monthly/daily returns) are only ever loaded when actually requested via
  `/backtests/{id}/equity`, not on every list/status call.
- `backtests` has a composite index on `(owner_id, status)` (not just the individual FK index on
  `owner_id`) for the "my running/completed backtests" dashboard query; `strategies.is_public` is
  independently indexed for the public-strategy-catalog filter. Both were added after finding the
  gap via `EXPLAIN`-style reasoning about actual query patterns, not just indexing every column.
- Every list endpoint that serializes a relationship (`WatchlistRead.items[].asset`,
  `AnalyticsService.compare`'s `backtest.strategy`) uses `selectinload`/`joinedload` explicitly —
  verified by a dedicated query-count regression test (`tests/unit/test_query_efficiency.py`)
  rather than assumed correct by inspection.
