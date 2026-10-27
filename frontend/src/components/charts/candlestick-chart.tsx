"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, CATEGORICAL, plotlyConfig, PlotlyTrace, STATUS, useChartMode } from "@/lib/chart-theme";
import type { OhlcvBar, Trade } from "@/types/api";

export function CandlestickChart({ bars, trades }: { bars: OhlcvBar[]; trades: Trade[] }) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const categorical = CATEGORICAL[mode];

    const candlestick: PlotlyTrace = {
      type: "candlestick",
      x: bars.map((b) => b.date),
      open: bars.map((b) => b.open),
      high: bars.map((b) => b.high),
      low: bars.map((b) => b.low),
      close: bars.map((b) => b.close),
      name: "Price",
      increasing: { line: { color: STATUS.good } },
      decreasing: { line: { color: STATUS.critical } },
    };

    const entries: PlotlyTrace = {
      type: "scatter",
      mode: "markers",
      name: "Entry",
      x: trades.map((t) => t.entry_date),
      y: trades.map((t) => t.entry_price),
      marker: { symbol: "triangle-up", size: 10, color: categorical[0], line: { width: 1, color: "#fff" } },
      hovertemplate: "Entry %{x}<br>$%{y:.2f}<extra></extra>",
    };

    const exits: PlotlyTrace = {
      type: "scatter",
      mode: "markers",
      name: "Exit",
      x: trades.map((t) => t.exit_date),
      y: trades.map((t) => t.exit_price),
      marker: {
        symbol: "triangle-down",
        size: 10,
        color: trades.map((t) => (t.pnl >= 0 ? STATUS.good : STATUS.critical)),
        line: { width: 1, color: "#fff" },
      },
      hovertemplate: "Exit %{x}<br>$%{y:.2f}<extra></extra>",
    };

    return {
      data: [candlestick, entries, exits],
      layout: {
        ...base,
        xaxis: { ...base.xaxis, rangeslider: { visible: false } },
        showlegend: true,
      },
    };
  }, [bars, trades, mode]);

  if (bars.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No price data available to chart.</p>;
  }

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
