"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, DIVERGING, plotlyConfig, PlotlyTrace, useChartMode } from "@/lib/chart-theme";
import type { MonthlyReturnPoint } from "@/types/api";

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function MonthlyHeatmapChart({ data }: { data: MonthlyReturnPoint[] }) {
  const mode = useChartMode();

  const { traces, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const diverging = DIVERGING[mode];

    const years = Array.from(new Set(data.map((d) => d.year))).sort();
    const matrix = years.map((year) =>
      MONTH_LABELS.map((_, i) => {
        const point = data.find((d) => d.year === year && d.month === i + 1);
        return point ? point.return_pct : null;
      }),
    );
    const maxAbs = Math.max(1, ...data.map((d) => Math.abs(d.return_pct)));

    const trace: PlotlyTrace = {
      type: "heatmap",
      x: MONTH_LABELS,
      y: years.map(String),
      z: matrix,
      zmid: 0,
      zmin: -maxAbs,
      zmax: maxAbs,
      colorscale: [
        [0, diverging.negative],
        [0.5, diverging.neutral],
        [1, diverging.positive],
      ],
      colorbar: { title: { text: "Return %" }, tickfont: { color: base.font.color } },
      hovertemplate: "%{y} %{x}<br>%{z:.2f}%<extra></extra>",
      xgap: 3,
      ygap: 3,
    };

    return {
      traces: [trace],
      layout: {
        ...base,
        yaxis: { ...base.yaxis, autorange: "reversed" as const },
      },
    };
  }, [data, mode]);

  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">Not enough history for a monthly view.</p>;
  }

  return (
    <Plot
      data={traces as Plotly.Data[]}
      layout={layout}
      config={plotlyConfig}
      useResizeHandler
      style={{ width: "100%", height: "320px" }}
    />
  );
}
