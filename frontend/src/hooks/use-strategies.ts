"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { strategiesApi } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function useStrategyCatalog() {
  return useQuery({ queryKey: ["strategies", "catalog"], queryFn: strategiesApi.catalog, staleTime: Infinity });
}

export function useStrategies(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["strategies", "list", page, pageSize],
    queryFn: () => strategiesApi.list(page, pageSize),
  });
}

export function useStrategy(id: number | null) {
  return useQuery({
    queryKey: ["strategies", id],
    queryFn: () => strategiesApi.get(id as number),
    enabled: id !== null,
  });
}

export function useCreateStrategy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: strategiesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies", "list"] });
      toast.success("Strategy saved");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteStrategy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: strategiesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies", "list"] });
      toast.success("Strategy deleted");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
