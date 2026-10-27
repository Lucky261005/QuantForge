import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    ...options,
  }).format(value);
}

export function formatPercent(value: number, decimals = 2): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatCompactNumber(value: number): string {
  // en-IN's compact notation naturally renders Indian units (L for lakh, Cr for crore)
  // instead of the Western K/M/B a US locale would produce.
  return new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function formatMarketCapCr(marketCapCr: number): string {
  // Market cap is already stored in INR crore (the unit Indian exchanges report in),
  // so this only needs a crore/lakh-crore label, not currency formatting from raw INR.
  if (marketCapCr >= 100_000) return `₹${(marketCapCr / 100_000).toFixed(2)}L Cr`;
  return `₹${marketCapCr.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
}

export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", ...options }).format(d);
}
