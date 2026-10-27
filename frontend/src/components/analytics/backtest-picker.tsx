"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { useBacktests } from "@/hooks/use-backtests";

interface BacktestPickerProps {
  selected: number[];
  onChange: (ids: number[]) => void;
}

export function BacktestPicker({ selected, onChange }: BacktestPickerProps) {
  const { data, isLoading } = useBacktests(1, 50);
  const completed = data?.items.filter((b) => b.status === "completed") ?? [];

  function toggle(id: number) {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  }

  if (isLoading) return <Skeleton className="h-32 w-full" />;

  if (completed.length === 0) {
    return <p className="text-sm text-muted-foreground">No completed backtests yet — run one from Strategy Builder.</p>;
  }

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {completed.map((backtest) => (
        <label
          key={backtest.id}
          className="flex cursor-pointer items-center gap-3 rounded-lg border border-border p-3 text-sm hover:bg-accent/40"
        >
          <Checkbox checked={selected.includes(backtest.id)} onCheckedChange={() => toggle(backtest.id)} />
          <div>
            <p className="font-medium">{backtest.name || `Backtest #${backtest.id}`}</p>
            <p className="text-xs text-muted-foreground">{backtest.symbols.join(", ")}</p>
          </div>
        </label>
      ))}
    </div>
  );
}
