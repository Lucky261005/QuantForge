"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { watchlistsApi } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function useWatchlists() {
  return useQuery({ queryKey: ["watchlists"], queryFn: watchlistsApi.list });
}

export function useCreateWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: watchlistsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] });
      toast.success("Watchlist created");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useAddWatchlistItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ watchlistId, symbol }: { watchlistId: number; symbol: string }) =>
      watchlistsApi.addItem(watchlistId, symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] });
      toast.success("Added to watchlist");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useRemoveWatchlistItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ watchlistId, itemId }: { watchlistId: number; itemId: number }) =>
      watchlistsApi.removeItem(watchlistId, itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["watchlists"] }),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: watchlistsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] });
      toast.success("Watchlist deleted");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
