"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateBacktest } from "@/hooks/use-backtests";
import type { Strategy } from "@/types/api";

const CHARGE_MODELS = [
  { value: "flat", label: "Flat commission (custom %)" },
  { value: "indian_equity_delivery", label: "Indian equity, delivery (STT, exchange, SEBI, stamp duty + GST)" },
  { value: "indian_equity_intraday", label: "Indian equity, intraday (STT, exchange, SEBI, stamp duty + GST)" },
];

function defaultStartDate() {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 2);
  return d.toISOString().slice(0, 10);
}
function defaultEndDate() {
  return new Date().toISOString().slice(0, 10);
}

export function BacktestFormDialog({ strategy, trigger }: { strategy: Strategy; trigger: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [symbols, setSymbols] = useState("RELIANCE");
  const [startDate, setStartDate] = useState(defaultStartDate());
  const [endDate, setEndDate] = useState(defaultEndDate());
  const [initialCapital, setInitialCapital] = useState(100_000);
  const [commissionPct, setCommissionPct] = useState(0.1);
  const [slippagePct, setSlippagePct] = useState(0.05);
  const [positionSizePct, setPositionSizePct] = useState(100);
  const [stopLossPct, setStopLossPct] = useState<string>("");
  const [takeProfitPct, setTakeProfitPct] = useState<string>("");
  const [benchmarkSymbol, setBenchmarkSymbol] = useState("NIFTY50");
  const [chargeModel, setChargeModel] = useState("flat");
  const [brokeragePct, setBrokeragePct] = useState(0);
  const createBacktest = useCreateBacktest();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const symbolList = symbols
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);
    if (symbolList.length === 0) return;

    createBacktest.mutate({
      strategy_id: strategy.id,
      name: `${strategy.name} - ${symbolList.join(", ")}`,
      symbols: symbolList,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      commission_pct: commissionPct / 100,
      slippage_pct: slippagePct / 100,
      position_size_pct: positionSizePct / 100,
      stop_loss_pct: stopLossPct ? Number(stopLossPct) / 100 : null,
      take_profit_pct: takeProfitPct ? Number(takeProfitPct) / 100 : null,
      benchmark_symbol: benchmarkSymbol.toUpperCase(),
      charge_model: chargeModel,
      brokerage_pct: chargeModel === "flat" ? undefined : brokeragePct / 100,
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Run backtest: {strategy.name}</DialogTitle>
          <DialogDescription>
            Data must already be downloaded/uploaded for each symbol before running.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="max-h-[65vh] space-y-4 overflow-y-auto pr-1">
          <div className="space-y-2">
            <Label htmlFor="symbols">Symbols (comma-separated)</Label>
            <Input
              id="symbols"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              placeholder="RELIANCE, TCS"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="start-date">Start date</Label>
              <Input id="start-date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">End date</Label>
              <Input id="end-date" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="capital">Initial capital (₹)</Label>
              <Input
                id="capital"
                type="number"
                min={1}
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="benchmark">Benchmark</Label>
              <Input id="benchmark" value={benchmarkSymbol} onChange={(e) => setBenchmarkSymbol(e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-2">
              <Label htmlFor="commission" className="text-xs">
                Commission (%)
              </Label>
              <Input
                id="commission"
                type="number"
                step={0.01}
                min={0}
                value={commissionPct}
                onChange={(e) => setCommissionPct(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="slippage" className="text-xs">
                Slippage (%)
              </Label>
              <Input
                id="slippage"
                type="number"
                step={0.01}
                min={0}
                value={slippagePct}
                onChange={(e) => setSlippagePct(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="position-size" className="text-xs">
                Position size (%)
              </Label>
              <Input
                id="position-size"
                type="number"
                min={1}
                max={100}
                value={positionSizePct}
                onChange={(e) => setPositionSizePct(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="space-y-2 rounded-xl border border-border p-4">
            <Label htmlFor="charge-model" className="text-xs">
              Transaction cost model
            </Label>
            <Select value={chargeModel} onValueChange={setChargeModel}>
              <SelectTrigger id="charge-model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CHARGE_MODELS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {chargeModel !== "flat" && (
              <div className="space-y-2 pt-1">
                <Label htmlFor="brokerage" className="text-xs">
                  Brokerage (%). Statutory STT, exchange, SEBI, stamp duty and GST charges are added automatically
                </Label>
                <Input
                  id="brokerage"
                  type="number"
                  step={0.01}
                  min={0}
                  value={brokeragePct}
                  onChange={(e) => setBrokeragePct(Number(e.target.value))}
                />
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 rounded-xl border border-border p-4">
            <div className="space-y-2">
              <Label htmlFor="stop-loss" className="text-xs">
                Stop loss (%, optional)
              </Label>
              <Input
                id="stop-loss"
                type="number"
                min={0}
                placeholder="None"
                value={stopLossPct}
                onChange={(e) => setStopLossPct(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="take-profit" className="text-xs">
                Take profit (%, optional)
              </Label>
              <Input
                id="take-profit"
                type="number"
                min={0}
                placeholder="None"
                value={takeProfitPct}
                onChange={(e) => setTakeProfitPct(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="submit" variant="gradient" disabled={createBacktest.isPending}>
              Run backtest
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
