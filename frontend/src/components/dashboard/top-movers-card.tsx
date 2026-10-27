"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketMovers } from "@/hooks/use-market-overview";
import { cn, formatDate, formatPercent } from "@/lib/utils";

function MoverList({ title, items }: { title: string; items: { symbol: string; changePct: number }[] }) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted-foreground">{title}</p>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No data yet.</p>
      ) : (
        <div className="space-y-1.5">
          {items.map((item) => (
            <div key={item.symbol} className="flex items-center justify-between text-sm">
              <span className="font-medium">{item.symbol}</span>
              <span className={cn("tabular-nums", item.changePct >= 0 ? "text-success" : "text-destructive")}>
                {formatPercent(item.changePct)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TopMoversCard() {
  const { gainers, losers, isLoading, asOf } = useMarketMovers();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top gainers and losers</CardTitle>
        {asOf && <p className="text-xs text-muted-foreground">Last close in data: {formatDate(asOf)}</p>}
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-6">
        {isLoading ? (
          <>
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </>
        ) : (
          <>
            <MoverList title="Top Gainers" items={gainers} />
            <MoverList title="Top Losers" items={losers} />
          </>
        )}
      </CardContent>
    </Card>
  );
}
