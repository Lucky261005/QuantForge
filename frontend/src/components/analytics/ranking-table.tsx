import { cn } from "@/lib/utils";
import type { CompareEntry } from "@/types/api";

export function RankingTable({ entries }: { entries: CompareEntry[] }) {
  const ranked = [...entries].sort((a, b) => b.metrics.sharpe_ratio - a.metrics.sharpe_ratio);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="py-2 pr-4 font-medium">Rank</th>
            <th className="py-2 pr-4 font-medium">Backtest</th>
            <th className="py-2 pr-4 font-medium">Strategy</th>
            <th className="py-2 pr-4 text-right font-medium">Total Return</th>
            <th className="py-2 pr-4 text-right font-medium">Sharpe</th>
            <th className="py-2 pr-4 text-right font-medium">Max Drawdown</th>
            <th className="py-2 text-right font-medium">Win Rate</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((entry, i) => (
            <tr key={entry.backtest_id} className="border-b border-border/50 last:border-0">
              <td className="py-2.5 pr-4 font-medium text-muted-foreground">#{i + 1}</td>
              <td className="py-2.5 pr-4 font-medium">{entry.name || `Backtest #${entry.backtest_id}`}</td>
              <td className="py-2.5 pr-4 text-muted-foreground">{entry.strategy_type}</td>
              <td
                className={cn(
                  "py-2.5 pr-4 text-right tabular-nums",
                  entry.metrics.total_return_pct >= 0 ? "text-success" : "text-destructive",
                )}
              >
                {entry.metrics.total_return_pct.toFixed(2)}%
              </td>
              <td className="py-2.5 pr-4 text-right tabular-nums font-medium">
                {entry.metrics.sharpe_ratio.toFixed(2)}
              </td>
              <td className="py-2.5 pr-4 text-right tabular-nums text-destructive">
                {entry.metrics.max_drawdown_pct.toFixed(2)}%
              </td>
              <td className="py-2.5 text-right tabular-nums">{entry.metrics.win_rate_pct.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
