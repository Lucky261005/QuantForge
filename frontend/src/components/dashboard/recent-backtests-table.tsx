"use client";

import { QueryError } from "@/components/query-error";
import { ArrowRight, Inbox } from "lucide-react";
import Link from "next/link";

import { BacktestStatusBadge } from "@/components/backtest-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBacktests } from "@/hooks/use-backtests";
import { formatDate } from "@/lib/utils";

export function RecentBacktestsTable() {
  const { data, isLoading, isError, error, refetch } = useBacktests(1, 5);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Recent backtests</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/backtests">
            View all <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : isError ? (
          <QueryError error={error} onRetry={() => refetch()} what="recent backtests" />
        ) : !data || data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
            <Inbox className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No backtests yet</p>
            <Button size="sm" variant="gradient" asChild className="mt-2">
              <Link href="/strategies">Build your first strategy</Link>
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 font-medium">Name</th>
                  <th className="pb-2 font-medium">Symbols</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Created</th>
                  <th className="relative pb-2">
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((backtest) => (
                  <tr key={backtest.id} className="border-b border-border/50 last:border-0">
                    <td className="py-3 font-medium">{backtest.name || `Backtest #${backtest.id}`}</td>
                    <td className="py-3 text-muted-foreground">{backtest.symbols.join(", ")}</td>
                    <td className="py-3">
                      <BacktestStatusBadge status={backtest.status} />
                    </td>
                    <td className="py-3 text-muted-foreground">{formatDate(backtest.created_at)}</td>
                    <td className="py-3 text-right">
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/backtests/${backtest.id}`}>View</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
