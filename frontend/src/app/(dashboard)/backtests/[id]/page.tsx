"use client";

import { AlertTriangle, ArrowLeft, Loader2, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { BacktestStatusBadge } from "@/components/backtest-status-badge";
import { QueryError } from "@/components/query-error";
import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { EquityDrawdownChart } from "@/components/charts/equity-drawdown-chart";
import { MetricsGrid } from "@/components/charts/metrics-grid";
import { MonthlyHeatmapChart } from "@/components/charts/monthly-heatmap-chart";
import { CostSensitivityTable, WalkForwardTable } from "@/components/charts/robustness-tables";
import { TradeBlotterTable } from "@/components/charts/trade-blotter-table";
import { TradeDistributionChart } from "@/components/charts/trade-distribution-chart";
import { SyntheticDataBadge } from "@/components/synthetic-data-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useBacktest,
  useBacktestEquity,
  useBacktestMetrics,
  useBacktestStatus,
  useBacktestTrades,
  useCostSensitivity,
  useWalkForward,
  useDeleteBacktest,
} from "@/hooks/use-backtests";
import { useOhlcv } from "@/hooks/use-market-data";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function BacktestDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const router = useRouter();

  const { data: backtest, isError: backtestFailed, error: backtestError } = useBacktest(id);
  const { data: status, isError: statusFailed, error: statusError, refetch: refetchStatus } = useBacktestStatus(id);
  const isCompleted = status?.status === "completed";
  const isFailed = status?.status === "failed";

  const { data: metrics } = useBacktestMetrics(id, isCompleted);
  const { data: equity } = useBacktestEquity(id, isCompleted);
  const { data: trades } = useBacktestTrades(id, isCompleted);
  const [tab, setTab] = useState("equity");
  const costs = useCostSensitivity(id, isCompleted && tab === "costs");
  const walkForward = useWalkForward(id, isCompleted && tab === "walk-forward");
  const deleteBacktest = useDeleteBacktest();

  const singleSymbol = backtest?.symbols.length === 1 ? backtest.symbols[0] : null;
  const { data: priceData } = useOhlcv(
    isCompleted ? singleSymbol : null,
    backtest?.start_date ?? "",
    backtest?.end_date ?? "",
  );
  const { data: benchmarkData } = useOhlcv(
    isCompleted ? backtest?.benchmark_symbol ?? null : null,
    backtest?.start_date ?? "",
    backtest?.end_date ?? "",
  );

  const benchmarkEquity = useMemo(() => {
    if (!benchmarkData || !backtest || benchmarkData.bars.length === 0) return undefined;
    const startClose = benchmarkData.bars[0].close;
    return benchmarkData.bars.map((bar) => ({
      date: bar.date,
      equity: (bar.close / startClose) * backtest.initial_capital,
    }));
  }, [benchmarkData, backtest]);

  function handleDelete() {
    if (!confirm("Delete this backtest and its results? This can't be undone.")) return;
    deleteBacktest.mutate(id, { onSuccess: () => router.push("/backtests") });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Button variant="ghost" size="sm" asChild className="-ml-2 mb-1">
            <Link href="/backtests">
              <ArrowLeft className="h-3.5 w-3.5" /> All backtests
            </Link>
          </Button>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold tracking-[-0.01em]">{backtest?.name ?? `Backtest #${id}`}</h2>
            {backtest && <SyntheticDataBadge symbols={backtest.symbols} />}
          </div>
          {backtest && (
            <p className="text-sm text-muted-foreground">
              {backtest.symbols.join(", ")} · {formatDate(backtest.start_date)} to {formatDate(backtest.end_date)} ·{" "}
              <span className="num">{formatCurrency(backtest.initial_capital, { maximumFractionDigits: 0 })}</span> initial capital
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {status && <BacktestStatusBadge status={status.status} />}
          <Button variant="outline" size="sm" onClick={handleDelete}>
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </Button>
        </div>
      </div>

      {(statusFailed || backtestFailed) && (
        <Card>
          <CardContent>
            <QueryError error={statusError ?? backtestError} onRetry={() => refetchStatus()} what="this backtest" />
          </CardContent>
        </Card>
      )}

      {!isCompleted && !isFailed && !statusFailed && !backtestFailed && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="font-medium">Running backtest...</p>
            <p className="text-sm text-muted-foreground">
              This usually takes a few seconds. The page updates automatically.
            </p>
          </CardContent>
        </Card>
      )}

      {isFailed && (
        <Card className="border-destructive/30">
          <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <p className="font-medium">This backtest failed</p>
            <p className="max-w-md text-sm text-muted-foreground">{status?.error_message}</p>
          </CardContent>
        </Card>
      )}

      {isCompleted && (
        <>
          {metrics ? <MetricsGrid metrics={metrics} /> : <Skeleton className="h-40 w-full" />}

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="no-scrollbar max-w-full justify-start overflow-x-auto">
              <TabsTrigger value="equity">Equity & Drawdown</TabsTrigger>
              {singleSymbol && <TabsTrigger value="price">Price & Trades</TabsTrigger>}
              <TabsTrigger value="monthly">Monthly Returns</TabsTrigger>
              <TabsTrigger value="trades">Trade Blotter</TabsTrigger>
              <TabsTrigger value="walk-forward">Walk-forward</TabsTrigger>
              <TabsTrigger value="costs">Cost Sensitivity</TabsTrigger>
            </TabsList>

            <TabsContent value="equity">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Equity vs benchmark</CardTitle>
                </CardHeader>
                <CardContent>
                  {equity ? (
                    <EquityDrawdownChart
                      equityCurve={equity.equity_curve}
                      drawdownCurve={equity.drawdown_curve}
                      benchmarkCurve={benchmarkEquity}
                    />
                  ) : (
                    <Skeleton className="h-[420px] w-full" />
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {singleSymbol && (
              <TabsContent value="price">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{singleSymbol}: entries and exits</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {priceData && trades ? (
                      <CandlestickChart bars={priceData.bars} trades={trades} />
                    ) : (
                      <Skeleton className="h-[420px] w-full" />
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            )}

            <TabsContent value="monthly">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Monthly returns</CardTitle>
                </CardHeader>
                <CardContent>
                  {equity ? (
                    <MonthlyHeatmapChart data={equity.monthly_returns} />
                  ) : (
                    <Skeleton className="h-80 w-full" />
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="trades" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Trade P&amp;L distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  {trades ? <TradeDistributionChart trades={trades} /> : <Skeleton className="h-60 w-full" />}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Trade blotter</CardTitle>
                </CardHeader>
                <CardContent>
                  {trades ? <TradeBlotterTable trades={trades} /> : <Skeleton className="h-60 w-full" />}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="walk-forward">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Walk-forward validation</CardTitle>
                </CardHeader>
                <CardContent>
                  <WalkForwardTable rows={walkForward.data} loading={walkForward.isLoading} error={walkForward.error} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="costs">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Cost sensitivity</CardTitle>
                </CardHeader>
                <CardContent>
                  <CostSensitivityTable
                    rows={costs.data}
                    loading={costs.isLoading}
                    error={costs.error}
                    indianCharges={backtest?.charge_model !== "flat"}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
