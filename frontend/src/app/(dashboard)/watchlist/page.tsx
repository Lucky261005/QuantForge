"use client";

import { QueryError } from "@/components/query-error";
import { Plus, Star, Trash2, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useAddWatchlistItem,
  useCreateWatchlist,
  useDeleteWatchlist,
  useRemoveWatchlistItem,
  useWatchlists,
} from "@/hooks/use-watchlists";
import { formatDate } from "@/lib/utils";

function AddSymbolForm({ watchlistId }: { watchlistId: number }) {
  const [symbol, setSymbol] = useState("");
  const addItem = useAddWatchlistItem();

  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (!symbol.trim()) return;
        addItem.mutate({ watchlistId, symbol: symbol.trim().toUpperCase() }, { onSuccess: () => setSymbol("") });
      }}
    >
      <Input
        placeholder="Add symbol (e.g. RELIANCE)"
        aria-label="Symbol to add"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
      />
      <Button type="submit" size="icon" variant="outline" disabled={addItem.isPending} aria-label="Add symbol">
        <Plus className="h-4 w-4" />
      </Button>
    </form>
  );
}

function NewWatchlistDialog() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const createWatchlist = useCreateWatchlist();

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="gradient">
          <Plus className="h-4 w-4" /> New watchlist
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Watchlist</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!name.trim()) return;
            createWatchlist.mutate(name.trim(), {
              onSuccess: () => {
                setOpen(false);
                setName("");
              },
            });
          }}
        >
          <Input placeholder="e.g. Banking leaders" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
          <DialogFooter className="mt-4">
            <Button type="submit" variant="gradient" disabled={createWatchlist.isPending}>
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function WatchlistPage() {
  const { data: watchlists, isLoading, isError, error, refetch } = useWatchlists();
  const removeItem = useRemoveWatchlistItem();
  const deleteWatchlist = useDeleteWatchlist();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Watchlists</h2>
          <p className="text-sm text-muted-foreground">Track symbols you&apos;re actively researching.</p>
        </div>
        <NewWatchlistDialog />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {[...Array(2)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <QueryError error={error} onRetry={() => refetch()} what="your watchlists" />
      ) : !watchlists || watchlists.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border py-16 text-center">
          <Star className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No watchlists yet. Create your first one above.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {watchlists.map((watchlist) => (
            <Card key={watchlist.id}>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{watchlist.name}</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  aria-label={`Delete watchlist ${watchlist.name}`}
                  onClick={() => {
                    if (confirm(`Delete the watchlist "${watchlist.name}"? This can't be undone.`))
                      deleteWatchlist.mutate(watchlist.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <AddSymbolForm watchlistId={watchlist.id} />

                {watchlist.items.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">No symbols yet.</p>
                ) : (
                  <div className="space-y-2">
                    {watchlist.items.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                      >
                        <div>
                          <p className="text-sm font-medium">{item.asset.symbol}</p>
                          <p className="text-xs text-muted-foreground">Added {formatDate(item.added_at)}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          aria-label={`Remove ${item.asset.symbol} from ${watchlist.name}`}
                          onClick={() => removeItem.mutate({ watchlistId: watchlist.id, itemId: item.id })}
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
