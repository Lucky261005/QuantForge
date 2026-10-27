"use client";

import { AlertTriangle, RotateCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";

/** Shown when a request fails, so a failure never looks like an empty list or an endless spinner. */
export function QueryError({
  error,
  onRetry,
  what = "this data",
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  what?: string;
  className?: string;
}) {
  return (
    <div role="alert" className={cn("flex flex-col items-center gap-3 py-12 text-center", className)}>
      <AlertTriangle aria-hidden className="h-6 w-6 text-destructive" />
      <p className="text-sm">
        Couldn&apos;t load {what}. <span className="text-muted-foreground">{getApiErrorMessage(error)}</span>
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RotateCw aria-hidden /> Try again
        </Button>
      )}
    </div>
  );
}
