import { cn, formatCurrency } from "@/lib/utils";
import type { BacktestMetrics } from "@/types/api";

function MetricTile({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "good" | "bad";
}) {
  return (
    <div className="-mb-px -mr-px border-b border-r border-border px-4 py-3.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "num mt-1.5 text-lg font-medium",
          tone === "good" && "text-success",
          tone === "bad" && "text-destructive",
        )}
      >
        {value}
      </dd>
    </div>
  );
}

function toneFor(value: number): "good" | "bad" {
  return value >= 0 ? "good" : "bad";
}

export function MetricsGrid({ metrics }: { metrics: BacktestMetrics }) {
  return (
    <dl className="grid grid-cols-2 overflow-hidden rounded-md border border-border bg-card sm:grid-cols-3 lg:grid-cols-6">
      <MetricTile label="Total return" value={`${metrics.total_return_pct.toFixed(2)}%`} tone={toneFor(metrics.total_return_pct)} />
      <MetricTile label="CAGR" value={`${metrics.cagr_pct.toFixed(2)}%`} tone={toneFor(metrics.cagr_pct)} />
      <MetricTile label="Volatility (ann.)" value={`${metrics.volatility_pct.toFixed(2)}%`} />
      <MetricTile label="Max drawdown" value={`${metrics.max_drawdown_pct.toFixed(2)}%`} tone="bad" />
      <MetricTile label="Sharpe" value={metrics.sharpe_ratio.toFixed(2)} tone={toneFor(metrics.sharpe_ratio)} />
      <MetricTile label="Sortino" value={metrics.sortino_ratio.toFixed(2)} tone={toneFor(metrics.sortino_ratio)} />
      <MetricTile label="Calmar" value={metrics.calmar_ratio.toFixed(2)} tone={toneFor(metrics.calmar_ratio)} />
      <MetricTile label="Omega" value={metrics.omega_ratio.toFixed(2)} />
      <MetricTile label="Ulcer index" value={metrics.ulcer_index.toFixed(2)} />
      <MetricTile label="VaR (95%)" value={`${metrics.var_95_pct.toFixed(2)}%`} tone="bad" />
      <MetricTile label="CVaR (95%)" value={`${metrics.cvar_95_pct.toFixed(2)}%`} tone="bad" />
      <MetricTile label="Max losing streak" value={String(metrics.max_consecutive_losses)} />
      <MetricTile label="Win rate" value={`${metrics.win_rate_pct.toFixed(1)}%`} tone={metrics.win_rate_pct >= 50 ? "good" : "bad"} />
      <MetricTile label="Profit factor" value={metrics.profit_factor.toFixed(2)} tone={toneFor(metrics.profit_factor - 1)} />
      <MetricTile label="Expectancy" value={formatCurrency(metrics.expectancy)} tone={toneFor(metrics.expectancy)} />
      <MetricTile label="Trades" value={String(metrics.num_trades)} />
      <MetricTile label="Alpha (ann.)" value={metrics.alpha.toFixed(3)} tone={toneFor(metrics.alpha)} />
      <MetricTile label="Beta" value={metrics.beta.toFixed(2)} />
    </dl>
  );
}
