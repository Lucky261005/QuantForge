import { AlertTriangle } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { getApiErrorMessage } from "@/lib/api-client";
import { cn, formatDate } from "@/lib/utils";
import type { CostSensitivityEntry, WalkForwardWindow } from "@/types/api";

const signed = (v: number | null, digits = 2) => (v === null ? "n/a" : `${v > 0 ? "+" : ""}${v.toFixed(digits)}`);
const tone = (v: number | null) => (v === null ? "" : v >= 0 ? "text-success" : "text-destructive");

function TableState({ loading, error }: { loading: boolean; error: unknown }) {
  if (loading) return <Skeleton className="h-48 w-full" />;
  return (
    <p role="alert" className="flex items-center gap-2 py-6 text-sm text-destructive">
      <AlertTriangle className="h-4 w-4" /> {getApiErrorMessage(error)}
    </p>
  );
}

export function CostSensitivityTable({
  rows,
  loading,
  error,
  indianCharges,
}: {
  rows: CostSensitivityEntry[] | undefined;
  loading: boolean;
  error: unknown;
  indianCharges: boolean;
}) {
  if (!rows) return <TableState loading={loading} error={error} />;
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        The same signals re-run with trading costs scaled from none to double.{" "}
        {indianCharges
          ? "Brokerage and slippage scale; statutory charges (STT, stamp duty, exchange fees, GST) stay as the law sets them."
          : "Commission and slippage both scale."}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th scope="col" className="py-2 pr-4 font-medium">Cost level</th>
              <th scope="col" className="py-2 pr-4 font-medium">Slippage</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Total return</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Sharpe</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Max drawdown</th>
              <th scope="col" className="py-2 text-right font-medium">Trades</th>
            </tr>
          </thead>
          <tbody className="num">
            {rows.map((r) => (
              <tr key={r.cost_multiplier} className={cn("border-b border-border", r.cost_multiplier === 1 && "bg-accent")}>
                <th scope="row" className="py-2 pr-4 text-left font-medium">
                  {r.cost_multiplier}× {r.cost_multiplier === 1 && <span className="text-xs text-muted-foreground">(as run)</span>}
                </th>
                <td className="py-2 pr-4">{(r.effective_slippage_pct * 100).toFixed(3)}%</td>
                <td className={cn("py-2 pr-4 text-right", tone(r.total_return_pct))}>{signed(r.total_return_pct)}%</td>
                <td className="py-2 pr-4 text-right">{r.sharpe_ratio.toFixed(2)}</td>
                <td className="py-2 pr-4 text-right text-destructive">{r.max_drawdown_pct.toFixed(2)}%</td>
                <td className="py-2 text-right">{r.num_trades}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function WalkForwardTable({
  rows,
  loading,
  error,
}: {
  rows: WalkForwardWindow[] | undefined;
  loading: boolean;
  error: unknown;
}) {
  if (!rows) return <TableState loading={loading} error={error} />;
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        The period split into {rows.length} back-to-back windows, each re-run with the same fixed parameters. Similar
        results across windows suggest the edge isn&rsquo;t tied to one market regime; parameters are not re-fitted per
        window.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th scope="col" className="py-2 pr-4 font-medium">Window</th>
              <th scope="col" className="py-2 pr-4 font-medium">Period</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Total return</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Sharpe</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Max drawdown</th>
              <th scope="col" className="py-2 text-right font-medium">Trades</th>
            </tr>
          </thead>
          <tbody className="num">
            {rows.map((w) => (
              <tr key={w.window} className="border-b border-border">
                <th scope="row" className="py-2 pr-4 text-left font-medium">{w.window}</th>
                <td className="whitespace-nowrap py-2 pr-4 font-sans text-muted-foreground">
                  {formatDate(w.start_date)} to {formatDate(w.end_date)}
                </td>
                {w.error ? (
                  <td colSpan={4} className="py-2 text-right font-sans text-muted-foreground">
                    Not enough data in this window
                  </td>
                ) : (
                  <>
                    <td className={cn("py-2 pr-4 text-right", tone(w.total_return_pct))}>{signed(w.total_return_pct)}%</td>
                    <td className="py-2 pr-4 text-right">{w.sharpe_ratio?.toFixed(2) ?? "n/a"}</td>
                    <td className="py-2 pr-4 text-right text-destructive">{w.max_drawdown_pct?.toFixed(2) ?? "n/a"}%</td>
                    <td className="py-2 text-right">{w.num_trades ?? "n/a"}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
