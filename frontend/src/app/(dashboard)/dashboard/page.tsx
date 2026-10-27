"use client";

import { KpiCard } from "@/components/dashboard/kpi-card";
import { MarketBreadthCard } from "@/components/dashboard/market-breadth-card";
import { MarketOverviewCard } from "@/components/dashboard/market-overview-card";
import { SyntheticDataNotice } from "@/components/synthetic-data-badge";
import { RecentBacktestsTable } from "@/components/dashboard/recent-backtests-table";
import { SectorPerformanceCard } from "@/components/dashboard/sector-performance-card";
import { TopMoversCard } from "@/components/dashboard/top-movers-card";
import { WatchlistStrip } from "@/components/dashboard/watchlist-strip";
import { useBacktests } from "@/hooks/use-backtests";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useWatchlists } from "@/hooks/use-watchlists";
import { formatCurrency } from "@/lib/utils";

export default function DashboardPage() {
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolio();
  const { data: backtests, isLoading: backtestsLoading } = useBacktests(1, 1);
  const { data: watchlists, isLoading: watchlistsLoading } = useWatchlists();

  const watchlistCount = watchlists?.reduce((sum, w) => sum + w.items.length, 0) ?? 0;

  return (
    <div className="space-y-6">
      <dl className="grid grid-cols-2 divide-border rounded-md border border-border bg-card lg:grid-cols-4 lg:divide-x [&>*:nth-child(-n+2)]:border-b [&>*:nth-child(-n+2)]:border-border lg:[&>*:nth-child(-n+2)]:border-b-0 [&>*:nth-child(odd)]:border-r [&>*:nth-child(odd)]:border-border">
        <KpiCard
          label="Cash balance"
          href="/portfolio"
          value={portfolio ? formatCurrency(portfolio.cash_balance) : "—"}
          loading={portfolioLoading}
        />
        <KpiCard
          label="Open positions"
          href="/portfolio"
          value={portfolio ? String(portfolio.holdings.length) : "—"}
          loading={portfolioLoading}
        />
        <KpiCard
          label="Backtests run"
          value={backtests ? String(backtests.total) : "—"}
          loading={backtestsLoading}
        />
        <KpiCard label="Watchlist symbols" value={String(watchlistCount)} loading={watchlistsLoading} />
      </dl>

      <SyntheticDataNotice />
      <MarketOverviewCard />
      <MarketBreadthCard />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <RecentBacktestsTable />
        </div>
        <WatchlistStrip />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <TopMoversCard />
        <SectorPerformanceCard />
      </div>
    </div>
  );
}
