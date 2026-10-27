import { MarketClock, Wordmark } from "@/components/brand";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_minmax(420px,520px)]">
      <aside className="relative hidden flex-col justify-between border-r border-border p-10 lg:flex">
        <Wordmark />
        <p aria-hidden className="display text-[clamp(2.5rem,4.5vw,4rem)] text-foreground">
          Before
          <br />
          the bell<span className="text-primary">.</span>
        </p>
        <div className="flex items-end justify-between gap-6">
          <p className="max-w-xs text-sm text-muted-foreground">
            Research and backtesting for NSE and BSE. Not connected to any broker, never places an order.
          </p>
          <MarketClock />
        </div>
      </aside>

      <div className="flex min-h-screen flex-col px-4 py-8 sm:px-10">
        <div className="flex items-center justify-between lg:hidden">
          <Wordmark />
          <MarketClock />
        </div>
        <main className="my-auto w-full max-w-md self-center py-12">{children}</main>
        <p className="text-center text-xs text-muted-foreground lg:hidden">
          Research platform, not connected to any broker.
        </p>
      </div>
    </div>
  );
}
