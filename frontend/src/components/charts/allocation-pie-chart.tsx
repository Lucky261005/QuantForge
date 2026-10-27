"use client";

import { useMemo } from "react";

import Plot from "@/components/charts/plot";
import { basePlotlyLayout, CATEGORICAL, PlotlyTrace, plotlyConfig, useChartMode } from "@/lib/chart-theme";

export function AllocationPieChart({ weights }: { weights: Record<string, number> }) {
  const mode = useChartMode();

  const { data, layout } = useMemo(() => {
    const base = basePlotlyLayout(mode);
    const categorical = CATEGORICAL[mode];
    const labels = Object.keys(weights);

    const trace: PlotlyTrace = {
      type: "pie",
      labels,
      values: labels.map((l) => weights[l] * 100),
      marker: { colors: labels.map((_, i) => categorical[i % categorical.length]) },
      textinfo: "label+percent",
      hovertemplate: "%{label}<br>%{value:.1f}%<extra></extra>",
      hole: 0.5,
    };

    return { data: [trace], layout: { ...base, showlegend: true } };
  }, [weights, mode]);

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
