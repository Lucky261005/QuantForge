"use client";

import { useEffect, useState } from "react";

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
import { useCreateStrategy } from "@/hooks/use-strategies";
import type { StrategyCatalogEntry } from "@/types/api";

interface StrategyFormDialogProps {
  catalog: StrategyCatalogEntry[];
  trigger: React.ReactNode;
  defaultOpen?: boolean;
}

export function StrategyFormDialog({ catalog, trigger, defaultOpen }: StrategyFormDialogProps) {
  const [open, setOpen] = useState(Boolean(defaultOpen));
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [strategyType, setStrategyType] = useState<string>("");
  const [params, setParams] = useState<Record<string, number>>({});
  const createStrategy = useCreateStrategy();

  const selected = catalog.find((c) => c.key === strategyType);

  useEffect(() => {
    if (selected) {
      setParams(Object.fromEntries(selected.params.map((p) => [p.name, p.default])));
    }
  }, [selected]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!strategyType || !name.trim()) return;
    createStrategy.mutate(
      { name, description: description || undefined, strategy_type: strategyType, parameters: params },
      {
        onSuccess: () => {
          setOpen(false);
          setName("");
          setDescription("");
          setStrategyType("");
          setParams({});
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>New Strategy</DialogTitle>
          <DialogDescription>
            Pick a strategy type and tune its parameters. You can reuse it across backtests.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="max-h-[60vh] space-y-4 overflow-y-auto pr-1">
          <div className="space-y-2">
            <Label>Strategy type</Label>
            <Select value={strategyType} onValueChange={setStrategyType}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a strategy..." />
              </SelectTrigger>
              <SelectContent>
                {catalog.map((entry) => (
                  <SelectItem key={entry.key} value={entry.key}>
                    {entry.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selected && <p className="text-xs text-muted-foreground">{selected.description}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="strategy-name">Name</Label>
            <Input
              id="strategy-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Fast MA cross, IT"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="strategy-description">Description (optional)</Label>
            <Input
              id="strategy-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Notes about this configuration..."
            />
          </div>

          {selected && selected.params.length > 0 && (
            <div className="space-y-3 rounded-xl border border-border p-4">
              <p className="text-xs font-medium text-muted-foreground">Parameters</p>
              <div className="grid grid-cols-2 gap-3">
                {selected.params.map((spec) => (
                  <div key={spec.name} className="space-y-1.5">
                    <Label htmlFor={`param-${spec.name}`} className="text-xs capitalize">
                      {spec.name.replaceAll("_", " ")}
                    </Label>
                    <Input
                      id={`param-${spec.name}`}
                      type="number"
                      step={spec.type === "int" ? 1 : 0.01}
                      min={spec.min ?? undefined}
                      max={spec.max ?? undefined}
                      value={params[spec.name] ?? spec.default}
                      onChange={(e) =>
                        setParams((prev) => ({ ...prev, [spec.name]: Number(e.target.value) }))
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <DialogFooter>
            <Button type="submit" variant="gradient" disabled={createStrategy.isPending || !strategyType}>
              Save strategy
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
