"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { notesApi } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api-client";

export function useNotes(page = 1, pageSize = 20) {
  return useQuery({ queryKey: ["notes", page, pageSize], queryFn: () => notesApi.list(page, pageSize) });
}

export function useCreateNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: notesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note saved");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; title?: string; content?: string; tags?: string[] }) =>
      notesApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notes"] }),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: notesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note deleted");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
