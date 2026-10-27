import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

/** Label that ticks up one line on hover/focus: the site's motion verb for primary targets. */
export function Roll({ children }: { children: string }) {
  return (
    <span className="relative inline-block overflow-hidden align-top leading-[1.2]">
      <span className="block transition-transform duration-200 ease-forge group-hover:-translate-y-full group-focus-visible:-translate-y-full motion-reduce:transition-none">
        {children}
      </span>
      <span
        aria-hidden
        className="absolute inset-x-0 top-full block transition-transform duration-200 ease-forge group-hover:-translate-y-full group-focus-visible:-translate-y-full motion-reduce:transition-none"
      >
        {children}
      </span>
    </span>
  );
}

export function RollButton({
  href,
  children,
  variant = "solid",
  className,
}: {
  href: string;
  children: string;
  variant?: "solid" | "line";
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group inline-flex h-12 items-center gap-3 rounded-md px-6 text-[15px] font-semibold transition-[color,background-color,border-color,transform] duration-150 ease-forge focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background active:scale-[0.97]",
        variant === "solid"
          ? "bg-primary text-primary-foreground hover:bg-foreground hover:text-background"
          : "border border-foreground/30 text-foreground hover:border-foreground hover:bg-foreground hover:text-background",
        className,
      )}
    >
      <Roll>{children}</Roll>
      <ArrowUpRight aria-hidden className="h-4 w-4 transition-transform duration-200 ease-forge group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
    </Link>
  );
}
