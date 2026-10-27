"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

/** A coin stamped with a Q: the rim is milled, the face carries the initial. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden className={className}>
      <circle cx="16" cy="16" r="15" fill="currentColor" />
      <circle cx="16" cy="16" r="12.25" fill="none" stroke="hsl(var(--primary-foreground))" strokeOpacity="0.35" strokeWidth="1" strokeDasharray="1.2 1.6" />
      {/* Q drawn as geometry so it sits on the coin's true centre (font glyphs sit off-centre) */}
      <g fill="none" stroke="hsl(var(--primary-foreground))" strokeWidth="3" strokeLinecap="round">
        <circle cx="16" cy="15.4" r="6.75" />
        <path d="M19.3 18.7 22.8 22.2" />
      </g>
    </svg>
  );
}

export function Wordmark({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <Link
      href="/"
      aria-label="QuantForge home"
      className={cn("group inline-flex min-h-6 items-center gap-2.5 py-1 text-foreground", className)}
    >
      <LogoMark className="h-10 w-10 text-primary transition-transform duration-200 ease-forge group-hover:-rotate-12 motion-reduce:transition-none" />
      {!compact && (
        <span className="text-xl font-semibold tracking-[-0.02em]">QuantForge</span>
      )}
    </Link>
  );
}

type Session = { label: string; open: boolean; time: string };

// NSE cash market: pre-open 09:00–09:15, continuous 09:15–15:30 IST, Mon–Fri.
// shortcut: exchange holidays are not modeled, so a holiday reads as "open"; add the NSE holiday list if this ever drives decisions.
export function nseSession(now: Date): Session {
  const ist = new Date(now.getTime() + (now.getTimezoneOffset() + 330) * 60_000);
  const mins = ist.getHours() * 60 + ist.getMinutes();
  const weekday = ist.getDay() >= 1 && ist.getDay() <= 5;
  const time = ist.toTimeString().slice(0, 8);
  if (weekday && mins >= 555 && mins < 930) return { label: "NSE open", open: true, time };
  if (weekday && mins >= 540 && mins < 555) return { label: "NSE pre-open", open: true, time };
  return { label: "NSE closed", open: false, time };
}

export function MarketClock({ className }: { className?: string }) {
  const [s, setS] = useState<Session | null>(null);
  useEffect(() => {
    const tick = () => setS(nseSession(new Date()));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <p className={cn("num inline-flex items-center gap-2 text-xs text-muted-foreground", className)}>
      <span
        aria-hidden
        className={cn("h-1.5 w-1.5 rounded-full", s?.open ? "bg-success" : "bg-muted-foreground/60")}
      />
      <span>{s ? s.label : "NSE"}</span>
      {/* the seconds tick is the page's idle motion; hidden from screen readers so it isn't announced every second */}
      <span aria-hidden className="text-foreground">
        {s ? s.time : "--:--:--"}
      </span>
      <span className="sr-only">India Standard Time</span>
      <span aria-hidden>IST</span>
    </p>
  );
}
