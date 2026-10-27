"use client";

import { useQueries } from "@tanstack/react-query";

import { useAssets } from "@/hooks/use-market-data";
import { assetsApi } from "@/lib/api";
import type { Asset, OhlcvBar } from "@/types/api";

const INDEX_SYMBOLS = ["NIFTY50", "BANKNIFTY", "SENSEX"];
export const INDEX_LABELS: Record<string, string> = { NIFTY50: "NIFTY 50", BANKNIFTY: "BANK NIFTY", SENSEX: "SENSEX" };

export interface Quote {
  symbol: string;
  last: number;
  changePct: number;
}

export interface SectorPerformance {
  sector: string;
  avgChangePct: number;
}

/** Two-week window ending at the asset's newest stored bar. Anchored to the data, not
 * today: stored history can end well before today (e.g. the static demo dataset). */
function windowEndingAt(latest: string) {
  const start = new Date(`${latest}T00:00:00Z`);
  start.setUTCDate(start.getUTCDate() - 14); // buffer past weekends/holidays for >=2 bars
  return { startDate: start.toISOString().slice(0, 10), endDate: latest };
}

function latestOf(assets: Asset[]): string | null {
  return assets.reduce<string | null>(
    (max, a) => (a.latest_bar_date && (!max || a.latest_bar_date > max) ? a.latest_bar_date : max),
    null,
  );
}

function recentBarsQuery(asset: Asset) {
  const { startDate, endDate } = windowEndingAt(asset.latest_bar_date as string);
  return {
    queryKey: ["assets", asset.symbol, "ohlcv", startDate, endDate],
    queryFn: () => assetsApi.getOhlcv(asset.symbol, startDate, endDate),
    staleTime: 60_000,
  };
}

function toQuote(symbol: string, bars: OhlcvBar[] | undefined): Quote | null {
  if (!bars || bars.length < 2) return null;
  const last = bars[bars.length - 1].close;
  const prev = bars[bars.length - 2].close;
  if (!prev) return null;
  return { symbol, last, changePct: ((last - prev) / prev) * 100 };
}

/** NIFTY/BANKNIFTY/SENSEX quote strip for the dashboard's market overview. */
export function useIndexQuotes() {
  const { data: assetsPage, isLoading: assetsLoading } = useAssets(1, 50);
  const indices = (assetsPage?.items ?? []).filter((a) => INDEX_SYMBOLS.includes(a.symbol) && a.latest_bar_date);
  const results = useQueries({ queries: indices.map(recentBarsQuery) });

  const isLoading = assetsLoading || results.some((r) => r.isLoading);
  const quotes = results
    .map((r, i) => toQuote(indices[i].symbol, r.data?.bars))
    .filter((q): q is Quote => q !== null);

  return { quotes, isLoading, asOf: latestOf(indices) };
}

/** Top gainers/losers and sector performance, derived from every seeded equity's
 * most recent two closes — computed client-side since this is a research/backtest
 * platform, not a live quote feed (see docs/ARCHITECTURE.md §7 for the live-price
 * extension seam). */
export function useMarketMovers() {
  const { data: assetsPage, isLoading: assetsLoading } = useAssets(1, 50);
  const equities = (assetsPage?.items ?? []).filter((a) => a.asset_type === "equity" && a.latest_bar_date);
  const results = useQueries({ queries: equities.map(recentBarsQuery) });

  const isLoading = assetsLoading || (equities.length > 0 && results.some((r) => r.isLoading));
  const quotes = results
    .map((r, i) => toQuote(equities[i].symbol, r.data?.bars))
    .filter((q): q is Quote => q !== null);

  const sorted = [...quotes].sort((a, b) => b.changePct - a.changePct);
  const gainers = sorted.slice(0, 5);
  const losers = sorted.slice(-5).reverse();

  const sectorChanges = new Map<string, number[]>();
  for (const asset of equities) {
    if (!asset.sector) continue;
    const quote = quotes.find((q) => q.symbol === asset.symbol);
    if (!quote) continue;
    const bucket = sectorChanges.get(asset.sector) ?? [];
    bucket.push(quote.changePct);
    sectorChanges.set(asset.sector, bucket);
  }
  const sectorPerformance: SectorPerformance[] = Array.from(sectorChanges.entries())
    .map(([sector, changes]) => ({
      sector,
      avgChangePct: changes.reduce((a: number, b: number) => a + b, 0) / changes.length,
    }))
    .sort((a, b) => b.avgChangePct - a.avgChangePct);

  return { gainers, losers, sectorPerformance, isLoading, asOf: latestOf(equities) };
}
