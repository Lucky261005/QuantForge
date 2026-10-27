"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { assetsApi } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function useAssets(page = 1, pageSize = 50) {
  return useQuery({ queryKey: ["assets", "list", page, pageSize], queryFn: () => assetsApi.list(page, pageSize) });
}

export function useMarketBreadth() {
  return useQuery({
    queryKey: ["assets", "breadth"],
    queryFn: assetsApi.getBreadth,
    staleTime: 60_000,
  });
}

export function useOhlcv(symbol: string | null, startDate: string, endDate: string) {
  return useQuery({
    queryKey: ["assets", symbol, "ohlcv", startDate, endDate],
    queryFn: () => assetsApi.getOhlcv(symbol as string, startDate, endDate),
    enabled: Boolean(symbol),
  });
}

export function useDownloadAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: assetsApi.download,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      toast.success(
        data.served_from_cache
          ? `${data.asset.symbol} already cached — no re-download needed`
          : `Downloaded ${data.bars_written} bars for ${data.asset.symbol}`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUploadAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ symbol, file }: { symbol: string; file: File }) => assetsApi.upload(symbol, file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      toast.success(`Uploaded ${data.bars_written} bars for ${data.asset.symbol}`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

/** Symbols whose stored prices are generated demo data (flagged by the API). */
export function useSyntheticSymbols(): Set<string> {
  const { data } = useAssets(1, 200);
  return new Set((data?.items ?? []).filter((a) => a.is_synthetic).map((a) => a.symbol));
}
