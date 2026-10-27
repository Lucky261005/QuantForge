"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

/** Fallback for errors on the public pages (home, auth). */
export default function RootError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main role="alert" className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <h1 className="display text-3xl">Something went wrong</h1>
      <p className="mt-3 text-sm text-muted-foreground">Please try again. If it keeps happening, reload the page.</p>
      <Button className="mt-6" onClick={reset}>
        Try again
      </Button>
    </main>
  );
}
