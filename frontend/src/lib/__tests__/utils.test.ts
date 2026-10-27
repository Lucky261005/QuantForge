import { describe, expect, it } from "vitest";

import { formatCurrency, formatPercent } from "@/lib/utils";

describe("formatCurrency", () => {
  it("uses rupees with Indian lakh grouping", () => {
    expect(formatCurrency(100000)).toBe("₹1,00,000.00");
    expect(formatCurrency(12345678.5)).toBe("₹1,23,45,678.50");
  });

  it("keeps the minus sign on losses", () => {
    expect(formatCurrency(-83.43)).toBe("-₹83.43");
  });
});

describe("formatPercent", () => {
  it("signs gains and losses", () => {
    expect(formatPercent(1.756)).toBe("+1.76%");
    expect(formatPercent(-0.18)).toBe("-0.18%");
    expect(formatPercent(0)).toBe("0.00%");
  });
});
