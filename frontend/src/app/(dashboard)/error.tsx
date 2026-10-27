"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

/** Catches render errors inside the app so one broken panel doesn't blank the whole screen. */
export default function DashboardError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div role="alert" className="mx-auto max-w-md py-24 text-center">
      <AlertTriangle aria-hidden className="mx-auto h-8 w-8 text-destructive" />
      <h2 className="mt-4 text-xl font-semibold">This page hit an error</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Your data is safe. Try again, or go back to the dashboard.
      </p>
      <div className="mt-6 flex justify-center gap-3">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" asChild>
          <Link href="/dashboard">Dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
