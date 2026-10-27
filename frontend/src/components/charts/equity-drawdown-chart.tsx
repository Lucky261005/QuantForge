"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, CATEGORICAL, DIVERGING, plotlyConfig, PlotlyTrace, useChartMode } from "@/lib/chart-theme";
import type { DrawdownPoint, EquityPoint } from "@/types/api";

function hexToRgba(hex: string, alpha: number) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

interface EquityDrawdownChartProps {
  equityCurve: EquityPoint[];
  drawdownCurve: DrawdownPoint[];
  benchmarkCurve?: EquityPoint[];
}

export function EquityDrawdownChart({ equityCurve, drawdownCurve, benchmarkCurve }: EquityDrawdownChartProps) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const categorical = CATEGORICAL[mode];
    const diverging = DIVERGING[mode];

    const equityDates = equityCurve.map((p) => p.date);
    const equityValues = equityCurve.map((p) => p.equity);
    const drawdownDates = drawdownCurve.map((p) => p.date);
    const drawdownValues = drawdownCurve.map((p) => p.drawdown_pct);

    const traces: PlotlyTrace[] = [
      {
        x: equityDates,
        y: equityValues,
        type: "scatter",
        mode: "lines",
        name: "Strategy Equity",
        line: { color: categorical[0], width: 2.5 },
        fill: "tozeroy",
        fillcolor: hexToRgba(categorical[0], 0.08),
        xaxis: "x",
        yaxis: "y",
        hovertemplate: "%{x}<br>$%{y:,.0f}<extra>Strategy</extra>",
      },
    ];

    if (benchmarkCurve && benchmarkCurve.length > 0) {
      traces.push({
        x: benchmarkCurve.map((p) => p.date),
        y: benchmarkCurve.map((p) => p.equity),
        type: "scatter",
        mode: "lines",
        name: "Benchmark",
        line: { color: categorical[1], width: 2, dash: "dot" },
        xaxis: "x",
        yaxis: "y",
        hovertemplate: "%{x}<br>$%{y:,.0f}<extra>Benchmark</extra>",
      });
    }

    traces.push({
      x: drawdownDates,
      y: drawdownValues,
      type: "scatter",
      mode: "lines",
      name: "Drawdown",
      line: { color: diverging.negative, width: 2 },
      fill: "tozeroy",
      fillcolor: hexToRgba(diverging.negative, 0.15),
      xaxis: "x2",
      yaxis: "y2",
      showlegend: false,
      hovertemplate: "%{x}<br>%{y:.1f}%<extra>Drawdown</extra>",
    });

    return {
      data: traces,
      layout: {
        ...base,
        grid: { rows: 2, columns: 1, pattern: "independent" as const },
        xaxis: { ...base.xaxis, anchor: "y", matches: "x2" },
        yaxis: { ...base.yaxis, domain: [0.38, 1], title: { text: "Equity (₹)" } },
        xaxis2: { ...base.xaxis, anchor: "y2" },
        yaxis2: { ...base.yaxis, domain: [0, 0.28], title: { text: "Drawdown (%)" } },
        showlegend: true,
      },
    };
  }, [equityCurve, drawdownCurve, benchmarkCurve, mode]);

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
