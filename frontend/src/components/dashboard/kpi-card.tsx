import Link from "next/link";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  loading?: boolean;
  trend?: "up" | "down" | "neutral";
  subtext?: string;
  href?: string;
}

/** One cell of the desk ledger strip: label over a tabular figure, divided by hairlines, not boxed. */
export function KpiCard({ label, value, loading, trend = "neutral", subtext, href }: KpiCardProps) {
  return (
    <div className="px-5 py-4">
      <dt className="text-xs text-muted-foreground">
        {href ? (
          <Link href={href} className="underline decoration-muted-foreground/40 underline-offset-4 hover:text-foreground">
            {label}
          </Link>
        ) : (
          label
        )}
      </dt>
      <dd className="mt-2">
        {loading ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <span
            className={cn(
              "num text-xl font-medium sm:text-2xl",
              trend === "up" && "text-success",
              trend === "down" && "text-destructive",
            )}
          >
            {value}
          </span>
        )}
        {subtext && <span className="mt-1 block text-xs text-muted-foreground">{subtext}</span>}
      </dd>
    </div>
  );
}
