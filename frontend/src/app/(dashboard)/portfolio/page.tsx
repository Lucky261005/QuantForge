"use client";

import { QueryError } from "@/components/query-error";
import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAssets } from "@/hooks/use-market-data";
import { usePortfolio, usePortfolioTransact, usePortfolioTransactions } from "@/hooks/use-portfolio";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Transaction } from "@/types/api";

type TxType = Transaction["type"];
const TYPE_LABELS: Record<TxType, string> = { buy: "Buy", sell: "Sell", deposit: "Deposit", withdraw: "Withdraw" };

function TransactionForm({ symbols }: { symbols: string[] }) {
  const transact = usePortfolioTransact();
  const [type, setType] = useState<TxType>("buy");
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [amount, setAmount] = useState("");
  const isTrade = type === "buy" || type === "sell";

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    transact.mutate(
      isTrade
        ? { type, symbol, quantity: Number(quantity), ...(price ? { price: Number(price) } : {}) }
        : { type, amount: Number(amount) },
      { onSuccess: () => (setQuantity(""), setPrice(""), setAmount("")) },
    );
  };

  return (
    <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 lg:items-end">
      <div className="space-y-2">
        <Label htmlFor="tx-type">Type</Label>
        <Select value={type} onValueChange={(v) => setType(v as TxType)}>
          <SelectTrigger id="tx-type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(TYPE_LABELS) as TxType[]).map((t) => (
              <SelectItem key={t} value={t}>
                {TYPE_LABELS[t]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isTrade ? (
        <>
          <div className="space-y-2">
            <Label htmlFor="tx-symbol">Symbol</Label>
            <Select value={symbol} onValueChange={setSymbol}>
              <SelectTrigger id="tx-symbol">
                <SelectValue placeholder="Choose a symbol" />
              </SelectTrigger>
              <SelectContent>
                {symbols.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="tx-qty">Quantity</Label>
            <Input id="tx-qty" type="number" min="0" step="any" required value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tx-price">Price (₹, optional)</Label>
            <Input
              id="tx-price"
              type="number"
              min="0"
              step="any"
              placeholder="Latest stored close"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
        </>
      ) : (
        <div className="space-y-2 lg:col-span-3">
          <Label htmlFor="tx-amount">Amount (₹)</Label>
          <Input id="tx-amount" type="number" min="0" step="any" required value={amount} onChange={(e) => setAmount(e.target.value)} />
        </div>
      )}

      <Button type="submit" variant="gradient" disabled={transact.isPending || (isTrade && !symbol)}>
        {transact.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
        Record {TYPE_LABELS[type].toLowerCase()}
      </Button>
    </form>
  );
}

export default function PortfolioPage() {
  const { data: portfolio, isLoading, isError, error, refetch } = usePortfolio();
  const { data: assetsPage } = useAssets(1, 200);
  const [page, setPage] = useState(1);
  const { data: history } = usePortfolioTransactions(page, 10);

  const symbolById = useMemo(
    () => new Map((assetsPage?.items ?? []).map((a) => [a.id, a.symbol])),
    [assetsPage],
  );
  const symbols = (assetsPage?.items ?? []).filter((a) => a.latest_bar_date).map((a) => a.symbol).sort();
  const invested = (portfolio?.holdings ?? []).reduce((sum, h) => sum + h.quantity * h.avg_price, 0);

  if (isError) {
    return <QueryError error={error} onRetry={() => refetch()} what="your portfolio" />;
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        A paper portfolio for tracking ideas. Nothing here places a real order or moves real money.
      </p>

      <dl className="grid grid-cols-2 rounded-md border border-border bg-card [&>*:first-child]:border-r [&>*:first-child]:border-border">
        <div className="px-5 py-4">
          <dt className="text-xs text-muted-foreground">Cash balance</dt>
          <dd className="num mt-2 text-xl font-medium sm:text-2xl">
            {isLoading ? <Skeleton className="h-7 w-24" /> : formatCurrency(portfolio?.cash_balance ?? 0)}
          </dd>
        </div>
        <div className="px-5 py-4">
          <dt className="text-xs text-muted-foreground">Invested at cost</dt>
          <dd className="num mt-2 text-xl font-medium sm:text-2xl">
            {isLoading ? <Skeleton className="h-7 w-24" /> : formatCurrency(invested)}
          </dd>
        </div>
      </dl>

      <Card>
        <CardHeader>
          <CardTitle>Record a transaction</CardTitle>
          <CardDescription>Buys and sells use the latest stored close unless you enter a price.</CardDescription>
        </CardHeader>
        <CardContent>
          <TransactionForm symbols={symbols} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          {!portfolio || portfolio.holdings.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No holdings yet. Record a buy above.</p>
          ) : (
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Holdings table">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th scope="col" className="py-2 pr-4 font-medium">Symbol</th>
                    <th scope="col" className="py-2 pr-4 text-right font-medium">Quantity</th>
                    <th scope="col" className="py-2 pr-4 text-right font-medium">Average price</th>
                    <th scope="col" className="py-2 text-right font-medium">Cost basis</th>
                  </tr>
                </thead>
                <tbody className="num">
                  {portfolio.holdings.map((h) => (
                    <tr key={h.id} className="border-b border-border">
                      <th scope="row" className="py-2 pr-4 text-left font-sans font-medium">
                        {symbolById.get(h.asset_id) ?? `Asset ${h.asset_id}`}
                      </th>
                      <td className="py-2 pr-4 text-right">{h.quantity}</td>
                      <td className="py-2 pr-4 text-right">{formatCurrency(h.avg_price)}</td>
                      <td className="py-2 text-right">{formatCurrency(h.quantity * h.avg_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>History</CardTitle>
        </CardHeader>
        <CardContent>
          {!history || history.items.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No transactions yet.</p>
          ) : (
            <>
              <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Transaction history table">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th scope="col" className="py-2 pr-4 font-medium">Date</th>
                      <th scope="col" className="py-2 pr-4 font-medium">Type</th>
                      <th scope="col" className="py-2 pr-4 font-medium">Symbol</th>
                      <th scope="col" className="py-2 pr-4 text-right font-medium">Quantity</th>
                      <th scope="col" className="py-2 pr-4 text-right font-medium">Price</th>
                      <th scope="col" className="py-2 text-right font-medium">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.items.map((t) => (
                      <tr key={t.id} className="border-b border-border">
                        <td className="whitespace-nowrap py-2 pr-4 text-muted-foreground">{formatDate(t.timestamp)}</td>
                        <td className="py-2 pr-4">{TYPE_LABELS[t.type]}</td>
                        <td className="py-2 pr-4">{t.asset_id ? symbolById.get(t.asset_id) ?? `Asset ${t.asset_id}` : "-"}</td>
                        <td className="num py-2 pr-4 text-right">{t.asset_id ? t.quantity : "-"}</td>
                        <td className="num py-2 pr-4 text-right">{t.asset_id ? formatCurrency(t.price) : "-"}</td>
                        <td className="num py-2 text-right">{formatCurrency(t.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {history.pages > 1 && (
                <div className="mt-4 flex items-center justify-end gap-2">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                    Previous
                  </Button>
                  <span className="text-xs text-muted-foreground">
                    Page {page} of {history.pages}
                  </span>
                  <Button variant="outline" size="sm" disabled={page >= history.pages} onClick={() => setPage((p) => p + 1)}>
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
