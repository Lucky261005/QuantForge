"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketMovers } from "@/hooks/use-market-overview";
import { DIVERGING, useChartMode } from "@/lib/chart-theme";
import { formatDate, formatPercent } from "@/lib/utils";

function hexToRgba(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function SectorPerformanceCard() {
  const { sectorPerformance, isLoading, asOf } = useMarketMovers();
  const mode = useChartMode();
  const diverging = DIVERGING[mode];
  const maxAbs = Math.max(1, ...sectorPerformance.map((s) => Math.abs(s.avgChangePct)));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sector heatmap</CardTitle>
        {asOf && <p className="text-xs text-muted-foreground">Last close in data: {formatDate(asOf)}</p>}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {[...Array(8)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : sectorPerformance.length === 0 ? (
          <p className="text-sm text-muted-foreground">No sector data yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {sectorPerformance.map((s) => {
              const up = s.avgChangePct >= 0;
              // Background alpha (not element opacity, which would also fade the
              // text) scales with magnitude relative to the day's biggest mover —
              // the strongest sector reads as the most saturated tile.
              const intensity = 0.12 + 0.33 * Math.min(1, Math.abs(s.avgChangePct) / maxAbs);
              const background = hexToRgba(up ? diverging.positive : diverging.negative, intensity);
              return (
                <div
                  key={s.sector}
                  className="flex flex-col justify-between rounded-lg border border-border p-3"
                  style={{ backgroundColor: background }}
                >
                  <span className="truncate text-xs font-medium text-foreground">{s.sector}</span>
                  <span
                    className="num mt-2 text-lg font-semibold text-foreground"
                  >
                    {formatPercent(s.avgChangePct)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
