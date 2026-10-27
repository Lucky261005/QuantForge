import { apiClient } from "@/lib/api-client";
import type {
  Asset,
  Backtest,
  BacktestEquity,
  BacktestMetrics,
  BacktestStatus,
  CompareResponse,
  CostSensitivityEntry,
  OptimizationMethod,
  OptimizeResponse,
  OhlcvBar,
  Page,
  Portfolio,
  ResearchNote,
  Strategy,
  StrategyCatalogEntry,
  Trade,
  Transaction,
  WalkForwardWindow,
  Watchlist,
} from "@/types/api";

// --- Auth ---
export const authApi = {
  register: (payload: { email: string; username: string; password: string; full_name?: string }) =>
    apiClient.post("/auth/register", payload).then((r) => r.data),
  login: (payload: { email: string; password: string }) =>
    apiClient.post("/auth/login", payload).then((r) => r.data),
  me: () => apiClient.get("/auth/me").then((r) => r.data),
  logout: (refresh_token: string) => apiClient.post("/auth/logout", { refresh_token }).then((r) => r.data),
  forgotPassword: (email: string) => apiClient.post("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (payload: { token: string; new_password: string }) =>
    apiClient.post("/auth/reset-password", payload).then((r) => r.data),
};

// --- Assets / Market Data ---
export const assetsApi = {
  list: (page = 1, pageSize = 20) =>
    apiClient.get<Page<Asset>>("/assets", { params: { page, page_size: pageSize } }).then((r) => r.data),
  download: (payload: { symbol: string; start_date: string; end_date: string; source?: string; force_refresh?: boolean }) =>
    apiClient.post("/assets/download", payload).then((r) => r.data),
  upload: (symbol: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient
      .post(`/assets/upload`, form, { params: { symbol }, headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
  getOhlcv: (symbol: string, startDate: string, endDate: string) =>
    apiClient
      .get<{ symbol: string; bars: OhlcvBar[] }>(`/assets/${symbol}/data`, {
        params: { start_date: startDate, end_date: endDate },
      })
      .then((r) => r.data),
  getBreadth: () =>
    apiClient
      .get<{
        advancing: number;
        declining: number;
        unchanged: number;
        new_52w_highs: number;
        new_52w_lows: number;
        total: number;
      }>("/assets/breadth")
      .then((r) => r.data),
};

// --- Strategies ---
export const strategiesApi = {
  catalog: () => apiClient.get<StrategyCatalogEntry[]>("/strategies/catalog").then((r) => r.data),
  list: (page = 1, pageSize = 20) =>
    apiClient.get<Page<Strategy>>("/strategies", { params: { page, page_size: pageSize } }).then((r) => r.data),
  get: (id: number) => apiClient.get<Strategy>(`/strategies/${id}`).then((r) => r.data),
  create: (payload: { name: string; description?: string; strategy_type: string; parameters: Record<string, number> }) =>
    apiClient.post<Strategy>("/strategies", payload).then((r) => r.data),
  update: (id: number, payload: Partial<{ name: string; description: string; parameters: Record<string, number> }>) =>
    apiClient.put<Strategy>(`/strategies/${id}`, payload).then((r) => r.data),
  delete: (id: number) => apiClient.delete(`/strategies/${id}`).then((r) => r.data),
};

// --- Backtests ---
export interface BacktestCreatePayload {
  strategy_id: number;
  name?: string;
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital?: number;
  commission_pct?: number;
  slippage_pct?: number;
  position_size_pct?: number;
  stop_loss_pct?: number | null;
  take_profit_pct?: number | null;
  benchmark_symbol?: string;
  charge_model?: string;
  brokerage_pct?: number;
}

export const backtestsApi = {
  create: (payload: BacktestCreatePayload) => apiClient.post<Backtest>("/backtests", payload).then((r) => r.data),
  list: (page = 1, pageSize = 20) =>
    apiClient.get<Page<Backtest>>("/backtests", { params: { page, page_size: pageSize } }).then((r) => r.data),
  get: (id: number) => apiClient.get<Backtest>(`/backtests/${id}`).then((r) => r.data),
  status: (id: number) =>
    apiClient
      .get<{ id: number; status: BacktestStatus; error_message: string | null; runtime_seconds: number | null }>(
        `/backtests/${id}/status`,
      )
      .then((r) => r.data),
  metrics: (id: number) => apiClient.get<BacktestMetrics>(`/backtests/${id}/metrics`).then((r) => r.data),
  equity: (id: number) => apiClient.get<BacktestEquity>(`/backtests/${id}/equity`).then((r) => r.data),
  trades: (id: number) => apiClient.get<Trade[]>(`/backtests/${id}/trades`).then((r) => r.data),
  costSensitivity: (id: number) =>
    apiClient.get<CostSensitivityEntry[]>(`/backtests/${id}/cost-sensitivity`).then((r) => r.data),
  walkForward: (id: number, nWindows = 4) =>
    apiClient
      .get<WalkForwardWindow[]>(`/backtests/${id}/walk-forward`, { params: { n_windows: nWindows } })
      .then((r) => r.data),
  delete: (id: number) => apiClient.delete(`/backtests/${id}`).then((r) => r.data),
};

// --- Analytics ---
export const analyticsApi = {
  compare: (backtestIds: number[]) =>
    apiClient.post<CompareResponse>("/analytics/compare", { backtest_ids: backtestIds }).then((r) => r.data),
  optimizePortfolio: (payload: {
    symbols: string[];
    start_date: string;
    end_date: string;
    method?: OptimizationMethod;
    risk_free_rate?: number;
  }) => apiClient.post<OptimizeResponse>("/analytics/optimize-portfolio", payload).then((r) => r.data),
};

// --- Watchlists ---
export const watchlistsApi = {
  list: () => apiClient.get<Watchlist[]>("/watchlists").then((r) => r.data),
  create: (name: string) => apiClient.post<Watchlist>("/watchlists", { name }).then((r) => r.data),
  addItem: (watchlistId: number, symbol: string) =>
    apiClient.post(`/watchlists/${watchlistId}/items`, { symbol }).then((r) => r.data),
  removeItem: (watchlistId: number, itemId: number) =>
    apiClient.delete(`/watchlists/${watchlistId}/items/${itemId}`).then((r) => r.data),
  delete: (watchlistId: number) => apiClient.delete(`/watchlists/${watchlistId}`).then((r) => r.data),
};

// --- Research Notes ---
export const notesApi = {
  list: (page = 1, pageSize = 20) =>
    apiClient.get<Page<ResearchNote>>("/notes", { params: { page, page_size: pageSize } }).then((r) => r.data),
  create: (payload: { title: string; content?: string; tags?: string[] }) =>
    apiClient.post<ResearchNote>("/notes", payload).then((r) => r.data),
  update: (id: number, payload: Partial<{ title: string; content: string; tags: string[] }>) =>
    apiClient.put<ResearchNote>(`/notes/${id}`, payload).then((r) => r.data),
  delete: (id: number) => apiClient.delete(`/notes/${id}`).then((r) => r.data),
};

// --- Portfolio ---
export const portfolioApi = {
  get: () => apiClient.get<Portfolio>("/portfolio").then((r) => r.data),
  transact: (payload: { type: string; symbol?: string; quantity?: number; price?: number; amount?: number }) =>
    apiClient.post<Portfolio>("/portfolio/transactions", payload).then((r) => r.data),
  transactions: (page = 1, pageSize = 20) =>
    apiClient
      .get<Page<Transaction>>("/portfolio/transactions", { params: { page, page_size: pageSize } })
      .then((r) => r.data),
};
