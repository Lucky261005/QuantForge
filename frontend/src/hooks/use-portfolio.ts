"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { portfolioApi } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function usePortfolio() {
  return useQuery({ queryKey: ["portfolio"], queryFn: portfolioApi.get });
}

export function usePortfolioTransactions(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["portfolio", "transactions", page, pageSize],
    queryFn: () => portfolioApi.transactions(page, pageSize),
  });
}

export function usePortfolioTransact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.transact,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      toast.success("Transaction executed");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
