"use client";

import { FlaskConical, Plus } from "lucide-react";

import { MarketDataPanel } from "@/components/strategy-builder/market-data-panel";
import { StrategyCard } from "@/components/strategy-builder/strategy-card";
import { StrategyFormDialog } from "@/components/strategy-builder/strategy-form-dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useStrategies, useStrategyCatalog } from "@/hooks/use-strategies";

export default function StrategiesPage() {
  const { data: catalog } = useStrategyCatalog();
  const { data: strategies, isLoading } = useStrategies(1, 50);

  return (
    <div className="space-y-6">
      <MarketDataPanel />

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Your Strategies</h2>
          <p className="text-sm text-muted-foreground">Saved, parameterized strategies ready to backtest.</p>
        </div>
        {catalog && (
          <StrategyFormDialog
            catalog={catalog}
            trigger={
              <Button variant="gradient">
                <Plus className="h-4 w-4" /> New strategy
              </Button>
            }
          />
        )}
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-56 w-full rounded-2xl" />
          ))}
        </div>
      ) : !strategies || strategies.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border py-16 text-center">
          <FlaskConical className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No strategies yet — create your first one above.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {strategies.items.map((strategy) => (
            <StrategyCard key={strategy.id} strategy={strategy} catalog={catalog ?? []} />
          ))}
        </div>
      )}
    </div>
  );
}
