"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { backtestsApi, type BacktestCreatePayload } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function useBacktests(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["backtests", "list", page, pageSize],
    queryFn: () => backtestsApi.list(page, pageSize),
  });
}

export function useBacktest(id: number) {
  return useQuery({ queryKey: ["backtests", id], queryFn: () => backtestsApi.get(id) });
}

/** Polls every 1.5s while the backtest is pending/running, stops once terminal or once the
 * request itself fails (the page then shows the error with a retry, not an endless spinner). */
export function useBacktestStatus(id: number) {
  return useQuery({
    queryKey: ["backtests", id, "status"],
    queryFn: () => backtestsApi.status(id),
    refetchInterval: (query) => {
      if (query.state.status === "error") return false;
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 1500;
    },
  });
}

export function useBacktestMetrics(id: number, enabled: boolean) {
  return useQuery({ queryKey: ["backtests", id, "metrics"], queryFn: () => backtestsApi.metrics(id), enabled });
}

export function useBacktestEquity(id: number, enabled: boolean) {
  return useQuery({ queryKey: ["backtests", id, "equity"], queryFn: () => backtestsApi.equity(id), enabled });
}

export function useBacktestTrades(id: number, enabled: boolean) {
  return useQuery({ queryKey: ["backtests", id, "trades"], queryFn: () => backtestsApi.trades(id), enabled });
}

// Both re-run the strategy server-side, so they only load when their tab is opened.
export function useCostSensitivity(id: number, enabled: boolean) {
  return useQuery({
    queryKey: ["backtests", id, "cost-sensitivity"],
    queryFn: () => backtestsApi.costSensitivity(id),
    enabled,
    staleTime: Infinity,
  });
}

export function useWalkForward(id: number, enabled: boolean) {
  return useQuery({
    queryKey: ["backtests", id, "walk-forward"],
    queryFn: () => backtestsApi.walkForward(id),
    enabled,
    staleTime: Infinity,
  });
}

export function useCreateBacktest() {
  const queryClient = useQueryClient();
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: BacktestCreatePayload) => backtestsApi.create(payload),
    onSuccess: (backtest) => {
      queryClient.invalidateQueries({ queryKey: ["backtests", "list"] });
      toast.success("Backtest started");
      router.push(`/backtests/${backtest.id}`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteBacktest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: backtestsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backtests", "list"] });
      toast.success("Backtest deleted");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
