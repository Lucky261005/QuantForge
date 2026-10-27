"use client";

import { Inbox } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { BacktestStatusBadge } from "@/components/backtest-status-badge";
import { QueryError } from "@/components/query-error";
import { SyntheticDataBadge } from "@/components/synthetic-data-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { useBacktests } from "@/hooks/use-backtests";
import { formatDate } from "@/lib/utils";

export default function BacktestsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useBacktests(page, 20);
  const [selected, setSelected] = useState<number[]>([]);

  function toggle(id: number) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Backtests</h2>
          <p className="text-sm text-muted-foreground">Every backtest you&apos;ve run, across every strategy.</p>
        </div>
        {selected.length >= 2 && (
          <Button variant="gradient" size="sm" asChild>
            <Link href={`/analytics?ids=${selected.join(",")}`}>Compare {selected.length} selected</Link>
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-6">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : isError ? (
            <QueryError error={error} onRetry={() => refetch()} what="your backtests" />
          ) : !data || data.items.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <Inbox className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No backtests yet.</p>
              <Button size="sm" variant="gradient" asChild>
                <Link href="/strategies">Build a strategy</Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="relative w-10 p-4">
                      <span className="sr-only">Select to compare</span>
                    </th>
                    <th className="p-4 font-medium">Name</th>
                    <th className="p-4 font-medium">Symbols</th>
                    <th className="hidden p-4 font-medium md:table-cell">Period</th>
                    <th className="hidden p-4 font-medium sm:table-cell">Status</th>
                    <th className="hidden p-4 font-medium lg:table-cell">Created</th>
                    <th className="relative hidden p-4 sm:table-cell">
                      <span className="sr-only">Open</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((backtest) => (
                    <tr key={backtest.id} className="border-b border-border/50 last:border-0 hover:bg-accent/30">
                      <td className="p-4">
                        <Checkbox
                          checked={selected.includes(backtest.id)}
                          onCheckedChange={() => toggle(backtest.id)}
                          disabled={backtest.status !== "completed"}
                          aria-label={`Select ${backtest.name || `backtest ${backtest.id}`} to compare`}
                        />
                      </td>
                      <td className="p-4 font-medium">
                        <Link
                          href={`/backtests/${backtest.id}`}
                          className="underline decoration-muted-foreground/30 underline-offset-4 hover:decoration-foreground"
                        >
                          {backtest.name || `Backtest #${backtest.id}`}
                        </Link>
                      </td>
                      <td className="p-4 text-muted-foreground">
                        <span className="flex flex-wrap items-center gap-2">
                          {backtest.symbols.join(", ")}
                          <SyntheticDataBadge symbols={backtest.symbols} />
                        </span>
                      </td>
                      <td className="hidden whitespace-nowrap p-4 text-muted-foreground md:table-cell">
                        {formatDate(backtest.start_date)} to {formatDate(backtest.end_date)}
                      </td>
                      <td className="hidden p-4 sm:table-cell">
                        <BacktestStatusBadge status={backtest.status} />
                      </td>
                      <td className="hidden whitespace-nowrap p-4 text-muted-foreground lg:table-cell">
                        {formatDate(backtest.created_at)}
                      </td>
                      <td className="hidden p-4 text-right sm:table-cell">
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

      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.page} of {data.pages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
