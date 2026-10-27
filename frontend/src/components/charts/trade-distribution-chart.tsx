"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, DIVERGING, PlotlyTrace, plotlyConfig, useChartMode } from "@/lib/chart-theme";
import type { Trade } from "@/types/api";

/** Histogram of per-trade P&L% — answers "is this strategy's edge a few big wins
 * or a consistent small edge repeated," which the trade blotter table (one row
 * per trade) makes tedious to eyeball once there are more than a dozen trades. */
export function TradeDistributionChart({ trades }: { trades: Trade[] }) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const diverging = DIVERGING[mode];
    const pnlPcts = trades.map((t) => t.pnl_pct * 100);

    const trace: PlotlyTrace = {
      type: "histogram",
      x: pnlPcts,
      marker: {
        color: pnlPcts.map((v) => (v >= 0 ? diverging.positive : diverging.negative)),
      },
      hovertemplate: "P&L: %{x:.2f}%<br>Trades: %{y}<extra></extra>",
    };

    return {
      data: [trace],
      layout: {
        ...base,
        bargap: 0.05,
        xaxis: { ...base.xaxis, title: { text: "Trade P&L (%)" }, zeroline: true, zerolinecolor: base.font.color },
        yaxis: { ...base.yaxis, title: { text: "Number of trades" } },
      },
    };
  }, [trades, mode]);

  if (trades.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No closed trades yet.</p>;
  }

  return (
    <Plot
      data={data as Plotly.Data[]}
      layout={layout}
      config={plotlyConfig}
      useResizeHandler
      style={{ width: "100%", height: "320px" }}
    />
  );
}
