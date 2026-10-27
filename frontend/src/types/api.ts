export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Asset {
  id: number;
  symbol: string;
  name: string | null;
  asset_type: string;
  exchange: string | null;
  currency: string;
  sector: string | null;
  industry: string | null;
  market_cap_cr: number | null;
  latest_bar_date: string | null;
  is_synthetic: boolean;
}

export interface OhlcvBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number;
  volume: number;
}

export interface ParamSpec {
  name: string;
  type: "int" | "float";
  default: number;
  min: number | null;
  max: number | null;
}

export interface StrategyCatalogEntry {
  key: string;
  label: string;
  description: string;
  params: ParamSpec[];
}

export interface Strategy {
  id: number;
  owner_id: number;
  name: string;
  description: string | null;
  strategy_type: string;
  parameters: Record<string, number>;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export type BacktestStatus = "pending" | "running" | "completed" | "failed";

export interface Backtest {
  id: number;
  owner_id: number;
  strategy_id: number;
  name: string | null;
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_pct: number;
  slippage_pct: number;
  position_size_pct: number;
  stop_loss_pct: number | null;
  take_profit_pct: number | null;
  benchmark_symbol: string;
  charge_model: "flat" | "indian_equity_delivery" | "indian_equity_intraday";
  brokerage_pct: number;
  status: BacktestStatus;
  strategy_version_hash: string | null;
  runtime_seconds: number | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface BacktestMetrics {
  total_return_pct: number;
  cagr_pct: number;
  volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  omega_ratio: number;
  max_drawdown_pct: number;
  ulcer_index: number;
  var_95_pct: number;
  cvar_95_pct: number;
  max_consecutive_losses: number;
  recovery_days: number | null;
  num_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  expectancy: number;
  alpha: number;
  beta: number;
}

export interface EquityPoint {
  date: string;
  equity: number;
}
export interface DrawdownPoint {
  date: string;
  drawdown_pct: number;
}
export interface MonthlyReturnPoint {
  year: number;
  month: number;
  return_pct: number;
}
export interface DailyReturnPoint {
  date: string;
  return_pct: number;
}

export interface BacktestEquity {
  equity_curve: EquityPoint[];
  drawdown_curve: DrawdownPoint[];
  monthly_returns: MonthlyReturnPoint[];
  daily_returns: DailyReturnPoint[];
}

export type TradeSide = "long" | "short";
export type ExitReason = "signal" | "stop_loss" | "take_profit" | "end_of_backtest";

export interface Trade {
  id: number;
  asset_id: number;
  side: TradeSide;
  entry_date: string;
  entry_price: number;
  exit_date: string;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct: number;
  exit_reason: ExitReason;
}

export interface CompareEntry {
  backtest_id: number;
  name: string | null;
  strategy_type: string;
  metrics: BacktestMetrics;
  equity_curve: EquityPoint[];
}

export interface CompareResponse {
  entries: CompareEntry[];
  correlation_matrix: Record<string, Record<string, number>>;
}

export type OptimizationMethod = "equal_weight" | "mean_variance" | "risk_parity" | "max_sharpe" | "min_volatility";

export interface OptimizeResponse {
  method: OptimizationMethod;
  weights: Record<string, number>;
  expected_return_pct: number;
  expected_volatility_pct: number;
  sharpe_ratio: number;
}

export interface Watchlist {
  id: number;
  name: string;
  created_at: string;
  items: WatchlistItem[];
}

export interface WatchlistItem {
  id: number;
  asset: Asset;
  added_at: string;
}

export interface ResearchNote {
  id: number;
  title: string;
  content: string;
  tags: string[];
  related_strategy_id: number | null;
  related_backtest_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface PortfolioHolding {
  id: number;
  asset_id: number;
  quantity: number;
  avg_price: number;
}

export interface Portfolio {
  id: number;
  name: string;
  cash_balance: number;
  holdings: PortfolioHolding[];
}

export interface Transaction {
  id: number;
  asset_id: number | null;
  type: "buy" | "sell" | "deposit" | "withdraw";
  quantity: number;
  price: number;
  amount: number;
  timestamp: string;
}

export interface CostSensitivityEntry {
  cost_multiplier: number;
  effective_commission_pct: number;
  effective_slippage_pct: number;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  num_trades: number;
}

export interface WalkForwardWindow {
  window: number;
  start_date: string;
  end_date: string;
  total_return_pct: number | null;
  sharpe_ratio: number | null;
  max_drawdown_pct: number | null;
  num_trades: number | null;
  error: string | null;
}
