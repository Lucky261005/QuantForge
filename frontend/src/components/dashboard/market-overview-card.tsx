"use client";

import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { INDEX_LABELS, useIndexQuotes } from "@/hooks/use-market-overview";
import { cn, formatDate, formatPercent } from "@/lib/utils";

export function MarketOverviewCard() {
  const { quotes, isLoading, asOf } = useIndexQuotes();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market overview</CardTitle>
        {asOf && <p className="text-xs text-muted-foreground">Last close in data: {formatDate(asOf)}</p>}
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {isLoading
          ? [...Array(3)].map((_, i) => <Skeleton key={i} className="h-[72px] w-full" />)
          : quotes.map((q) => {
              const up = q.changePct >= 0;
              return (
                <div key={q.symbol} className="rounded-lg border border-border p-3">
                  <p className="text-xs text-muted-foreground">{INDEX_LABELS[q.symbol] ?? q.symbol}</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">
                    {q.last.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                  </p>
                  <p
                    className={cn(
                      "flex items-center gap-1 text-xs font-medium",
                      up ? "text-success" : "text-destructive",
                    )}
                  >
                    {up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {formatPercent(q.changePct)}
                  </p>
                </div>
              );
            })}
        {!isLoading && quotes.length === 0 && (
          <p className="col-span-3 py-2 text-sm text-muted-foreground">
            No index data yet. Load NIFTY 50, BANK NIFTY or SENSEX in the Strategy Builder to fill this in.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
