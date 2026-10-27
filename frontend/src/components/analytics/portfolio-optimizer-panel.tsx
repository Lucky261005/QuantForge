"use client";

import { Sliders } from "lucide-react";
import { useState } from "react";

import { AllocationPieChart } from "@/components/charts/allocation-pie-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useOptimizePortfolio } from "@/hooks/use-analytics";
import type { OptimizationMethod } from "@/types/api";

const methods: { value: OptimizationMethod; label: string }[] = [
  { value: "max_sharpe", label: "Max Sharpe" },
  { value: "min_volatility", label: "Min Volatility" },
  { value: "risk_parity", label: "Risk Parity" },
  { value: "mean_variance", label: "Mean-Variance" },
  { value: "equal_weight", label: "Equal Weight" },
];

function defaultStart() {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 2);
  return d.toISOString().slice(0, 10);
}

export function PortfolioOptimizerPanel() {
  const [symbols, setSymbols] = useState("RELIANCE, TCS, HDFCBANK");
  const [startDate, setStartDate] = useState(defaultStart());
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [method, setMethod] = useState<OptimizationMethod>("max_sharpe");
  const optimize = useOptimizePortfolio();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const symbolList = symbols
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);
    if (symbolList.length < 2) return;
    optimize.mutate({ symbols: symbolList, start_date: startDate, end_date: endDate, method });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sliders className="h-4 w-4" /> Portfolio Optimizer
        </CardTitle>
        <CardDescription>
          Solve for allocation weights across a symbol universe — data must already be downloaded for each symbol.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1.5 lg:col-span-2">
            <Label className="text-xs">Symbols (comma-separated)</Label>
            <Input value={symbols} onChange={(e) => setSymbols(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Start date</Label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">End date</Label>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Method</Label>
            <Select value={method} onValueChange={(v) => setMethod(v as OptimizationMethod)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {methods.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="sm:col-span-2 lg:col-span-5">
            <Button type="submit" variant="gradient" disabled={optimize.isPending}>
              Optimize
            </Button>
          </div>
        </form>

        {optimize.data && (
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <AllocationPieChart weights={optimize.data.weights} />
            <div className="grid grid-cols-3 gap-3 self-start">
              <div className="rounded-xl border border-border p-4">
                <p className="text-xs text-muted-foreground">Expected Return</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {optimize.data.expected_return_pct.toFixed(2)}%
                </p>
              </div>
              <div className="rounded-xl border border-border p-4">
                <p className="text-xs text-muted-foreground">Expected Volatility</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {optimize.data.expected_volatility_pct.toFixed(2)}%
                </p>
              </div>
              <div className="rounded-xl border border-border p-4">
                <p className="text-xs text-muted-foreground">Sharpe</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">{optimize.data.sharpe_ratio.toFixed(2)}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
