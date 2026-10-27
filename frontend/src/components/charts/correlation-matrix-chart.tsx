"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, DIVERGING, PlotlyTrace, plotlyConfig, useChartMode } from "@/lib/chart-theme";

export function CorrelationMatrixChart({ matrix }: { matrix: Record<string, Record<string, number>> }) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const diverging = DIVERGING[mode];
    const labels = Object.keys(matrix);
    const z = labels.map((row) => labels.map((col) => matrix[row][col]));

    const trace: PlotlyTrace = {
      type: "heatmap",
      x: labels,
      y: labels,
      z,
      zmin: -1,
      zmax: 1,
      zmid: 0,
      colorscale: [
        [0, diverging.negative],
        [0.5, diverging.neutral],
        [1, diverging.positive],
      ],
      colorbar: { title: { text: "Correlation" } },
      text: z.map((row) => row.map((v) => v.toFixed(2))),
      texttemplate: "%{text}",
      textfont: { color: base.font.color },
      hovertemplate: "%{y} vs %{x}<br>%{z:.2f}<extra></extra>",
      xgap: 3,
      ygap: 3,
    };

    return { data: [trace], layout: { ...base, yaxis: { ...base.yaxis, autorange: "reversed" as const } } };
  }, [matrix, mode]);

  return (
    <Plot
      data={data as Plotly.Data[]}
      layout={layout}
      config={plotlyConfig}
      useResizeHandler
      style={{ width: "100%", height: "360px" }}
    />
  );
}
