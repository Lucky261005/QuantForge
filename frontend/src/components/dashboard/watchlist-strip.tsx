"use client";

import { Star } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWatchlists } from "@/hooks/use-watchlists";

export function WatchlistStrip() {
  const { data: watchlists, isLoading } = useWatchlists();
  const items = watchlists?.[0]?.items ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>{watchlists?.[0]?.name ?? "Watchlist"}</CardTitle>
        <Link href="/watchlist" className="inline-block py-1 text-xs text-primary underline decoration-primary/40 underline-offset-4 hover:decoration-primary">
          Manage
        </Link>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex gap-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-9 w-20 rounded-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <Star className="h-4 w-4" />
            No symbols yet. Add some from the Watchlist page.
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {items.map((item) => (
              <span
                key={item.id}
                className="rounded-full border border-border bg-muted/50 px-3 py-1.5 text-sm font-medium"
              >
                {item.asset.symbol}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
