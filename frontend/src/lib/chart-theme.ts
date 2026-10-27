"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

/** @types/plotly.js's `PlotData` doesn't declare every trace-type-specific field
 * (candlestick OHLC, heatmap z/zmid, etc.) — traces are built as plain objects
 * and cast to `Plotly.Data[]` once at the `<Plot data={...} />` call site. */
export type PlotlyTrace = Record<string, unknown>;

/** Validated categorical palette (see dataviz skill references/palette.md) —
 * fixed hue order, never cycled/reassigned per series. */
export const CATEGORICAL = {
  light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
  dark: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
};

export const DIVERGING = {
  light: { negative: "#e34948", neutral: "#f0efec", positive: "#2a78d6" },
  dark: { negative: "#e66767", neutral: "#383835", positive: "#3987e5" },
};

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const CHROME = {
  light: {
    surface: "#ffffff",
    primaryInk: "#0b0b0b",
    secondaryInk: "#52514e",
    mutedInk: "#898781",
    gridline: "#e1e0d9",
    baseline: "#c3c2b7",
  },
  dark: {
    surface: "#141c1f",
    primaryInk: "#ffffff",
    secondaryInk: "#c3c2b7",
    mutedInk: "#898781",
    gridline: "#2c2c2a",
    baseline: "#383835",
  },
};

export function useChartMode(): "light" | "dark" {
  const { resolvedTheme } = useTheme();
  const [mode, setMode] = useState<"light" | "dark">("dark");
  useEffect(() => setMode(resolvedTheme === "light" ? "light" : "dark"), [resolvedTheme]);
  return mode;
}

export function basePlotlyLayout(mode: "light" | "dark") {
  const chrome = CHROME[mode];
  return {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: chrome.secondaryInk, family: "var(--font-geist-sans), system-ui, sans-serif", size: 12 },
    margin: { t: 24, r: 24, b: 40, l: 56 },
    xaxis: {
      gridcolor: chrome.gridline,
      linecolor: chrome.baseline,
      zeroline: false,
      tickfont: { color: chrome.mutedInk },
    },
    yaxis: {
      gridcolor: chrome.gridline,
      linecolor: chrome.baseline,
      zeroline: false,
      tickfont: { color: chrome.mutedInk },
    },
    legend: { orientation: "h" as const, y: -0.2, font: { color: chrome.secondaryInk } },
    hoverlabel: {
      bgcolor: chrome.surface,
      bordercolor: chrome.gridline,
      font: { color: chrome.primaryInk },
    },
  };
}

export const plotlyConfig = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d"] };
