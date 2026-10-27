"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketBreadth } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

export function MarketBreadthCard() {
  const { data, isLoading } = useMarketBreadth();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market breadth</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const stats = [
    { label: "Advancing", value: data?.advancing ?? 0, tone: "success" as const, icon: ArrowUpRight },
    { label: "Declining", value: data?.declining ?? 0, tone: "destructive" as const, icon: ArrowDownRight },
    { label: "Unchanged", value: data?.unchanged ?? 0, tone: "muted" as const, icon: Minus },
    { label: "52W Highs", value: data?.new_52w_highs ?? 0, tone: "success" as const, icon: ArrowUpRight },
    { label: "52W Lows", value: data?.new_52w_lows ?? 0, tone: "destructive" as const, icon: ArrowDownRight },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market breadth</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 sm:grid-cols-5 sm:divide-x sm:divide-border">
        {stats.map((stat) => (
          <div key={stat.label} className="flex items-baseline gap-2 py-2 sm:px-4 sm:first:pl-0">
            <stat.icon
              className={cn(
                "h-3.5 w-3.5 shrink-0 self-center",
                stat.tone === "success" && "text-success",
                stat.tone === "destructive" && "text-destructive",
                stat.tone === "muted" && "text-muted-foreground",
              )}
            />
            <p
              className={cn(
                "num text-xl font-medium",
                stat.tone === "success" && "text-success",
                stat.tone === "destructive" && "text-destructive",
              )}
            >
              {stat.value}
            </p>
            <p className="text-xs text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
