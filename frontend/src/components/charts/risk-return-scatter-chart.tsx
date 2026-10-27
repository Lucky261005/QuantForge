"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, CATEGORICAL, PlotlyTrace, plotlyConfig, useChartMode } from "@/lib/chart-theme";
import type { CompareEntry } from "@/types/api";

/** One point per strategy: volatility (risk) on x, total return on y, marker size
 * scaled by Sharpe — the classic risk/return frontier view, so "which strategy
 * won" and "at what risk cost" read from the same chart instead of a table. */
export function RiskReturnScatterChart({ entries }: { entries: CompareEntry[] }) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const categorical = CATEGORICAL[mode];

    const sharpes = entries.map((e) => e.metrics.sharpe_ratio);
    const maxAbsSharpe = Math.max(1, ...sharpes.map((s) => Math.abs(s)));

    const traces: PlotlyTrace[] = entries.map((entry, i) => ({
      type: "scatter",
      mode: "markers+text",
      name: entry.name || `Backtest #${entry.backtest_id}`,
      x: [entry.metrics.volatility_pct],
      y: [entry.metrics.total_return_pct],
      text: [entry.name || `#${entry.backtest_id}`],
      textposition: "top center",
      marker: {
        color: categorical[i % categorical.length],
        size: 14 + 26 * (Math.abs(entry.metrics.sharpe_ratio) / maxAbsSharpe),
        line: { color: base.font.color, width: 1 },
      },
      hovertemplate:
        "%{text}<br>Volatility: %{x:.1f}%<br>Return: %{y:.1f}%<br>Sharpe: " +
        entry.metrics.sharpe_ratio.toFixed(2) +
        "<extra></extra>",
    }));

    return {
      data: traces,
      layout: {
        ...base,
        showlegend: false,
        xaxis: { ...base.xaxis, title: { text: "Volatility (annualized %)" } },
        yaxis: { ...base.yaxis, title: { text: "Total return (%)" } },
      },
    };
  }, [entries, mode]);

  return (
    <Plot
      data={data as Plotly.Data[]}
      layout={layout}
      config={plotlyConfig}
      useResizeHandler
      style={{ width: "100%", height: "380px" }}
    />
  );
}
