"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, CATEGORICAL, PlotlyTrace, plotlyConfig, useChartMode } from "@/lib/chart-theme";
import type { CompareEntry } from "@/types/api";

export function CompareEquityChart({ entries }: { entries: CompareEntry[] }) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const categorical = CATEGORICAL[mode];

    const traces: PlotlyTrace[] = entries.slice(0, 8).map((entry, i) => ({
      type: "scatter",
      mode: "lines",
      name: entry.name || `Backtest #${entry.backtest_id}`,
      x: entry.equity_curve.map((p) => p.date),
      y: entry.equity_curve.map((p) => p.equity),
      line: { color: categorical[i], width: 2.25 },
      hovertemplate: "%{x}<br>$%{y:,.0f}<extra>" + (entry.name || `#${entry.backtest_id}`) + "</extra>",
    }));

    return { data: traces, layout: { ...base, showlegend: true } };
  }, [entries, mode]);

  return (
    <Plot
      data={data as Plotly.Data[]}
      layout={layout}
      config={plotlyConfig}
      useResizeHandler
      style={{ width: "100%", height: "420px" }}
    />
  );
}
