"use client";

import { GitCompare } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { BacktestPicker } from "@/components/analytics/backtest-picker";
import { PortfolioOptimizerPanel } from "@/components/analytics/portfolio-optimizer-panel";
import { RankingTable } from "@/components/analytics/ranking-table";
import { CompareEquityChart } from "@/components/charts/compare-equity-chart";
import { CorrelationMatrixChart } from "@/components/charts/correlation-matrix-chart";
import { RiskReturnScatterChart } from "@/components/charts/risk-return-scatter-chart";
import { SyntheticDataNotice } from "@/components/synthetic-data-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCompareBacktests } from "@/hooks/use-analytics";

export default function AnalyticsPage() {
  const searchParams = useSearchParams();
  const [selected, setSelected] = useState<number[]>([]);
  const compare = useCompareBacktests();

  useEffect(() => {
    const ids = searchParams.get("ids");
    if (ids) {
      const parsed = ids.split(",").map(Number).filter(Boolean);
      setSelected(parsed);
      if (parsed.length >= 2) compare.mutate(parsed);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <div className="space-y-6">
      <SyntheticDataNotice />
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-4 w-4" /> Compare backtests
          </CardTitle>
          <CardDescription>Select at least two completed backtests to overlay and rank.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <BacktestPicker selected={selected} onChange={setSelected} />
          <Button
            variant="gradient"
            disabled={selected.length < 2 || compare.isPending}
            onClick={() => compare.mutate(selected)}
          >
            Compare {selected.length > 0 && `(${selected.length})`}
          </Button>
        </CardContent>
      </Card>

      {compare.data && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Equity curves</CardTitle>
            </CardHeader>
            <CardContent>
              <CompareEquityChart entries={compare.data.entries} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ranking</CardTitle>
            </CardHeader>
            <CardContent>
              <RankingTable entries={compare.data.entries} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Correlation matrix</CardTitle>
              <CardDescription>Daily return correlation between selected backtests.</CardDescription>
            </CardHeader>
            <CardContent>
              <CorrelationMatrixChart matrix={compare.data.correlation_matrix} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Risk vs return</CardTitle>
              <CardDescription>Volatility vs total return, marker size scaled by Sharpe ratio.</CardDescription>
            </CardHeader>
            <CardContent>
              <RiskReturnScatterChart entries={compare.data.entries} />
            </CardContent>
          </Card>
        </>
      )}

      <PortfolioOptimizerPanel />
    </div>
  );
}
