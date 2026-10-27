"use client";

import { Play, Trash2 } from "lucide-react";

import { BacktestFormDialog } from "@/components/strategy-builder/backtest-form-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDeleteStrategy } from "@/hooks/use-strategies";
import type { Strategy, StrategyCatalogEntry } from "@/types/api";

export function StrategyCard({ strategy, catalog }: { strategy: Strategy; catalog: StrategyCatalogEntry[] }) {
  const deleteStrategy = useDeleteStrategy();
  const catalogEntry = catalog.find((c) => c.key === strategy.strategy_type);

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle className="text-base">{strategy.name}</CardTitle>
          <Badge variant="outline" className="mt-2">
            {catalogEntry?.label ?? strategy.strategy_type}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-destructive"
          onClick={() => deleteStrategy.mutate(strategy.id)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-between">
        <div>
          {strategy.description && <p className="text-sm text-muted-foreground">{strategy.description}</p>}
          <div className="mt-3 flex flex-wrap gap-1.5">
            {Object.entries(strategy.parameters).map(([key, value]) => (
              <span key={key} className="rounded-md bg-muted px-2 py-1 text-xs tabular-nums text-muted-foreground">
                {key.replaceAll("_", " ")}: {value}
              </span>
            ))}
          </div>
        </div>

        <BacktestFormDialog
          strategy={strategy}
          trigger={
            <Button variant="gradient" size="sm" className="mt-4 w-full">
              <Play className="h-3.5 w-3.5" /> Run backtest
            </Button>
          }
        />
      </CardContent>
    </Card>
  );
}
