"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { analyticsApi } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function useCompareBacktests() {
  return useMutation({
    mutationFn: analyticsApi.compare,
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useOptimizePortfolio() {
  return useMutation({
    mutationFn: analyticsApi.optimizePortfolio,
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
