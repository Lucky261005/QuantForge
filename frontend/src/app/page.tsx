import type { Metadata } from "next";

import { LogoMark } from "@/components/brand";
import { Footer } from "@/components/marketing/footer";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import { RollButton } from "@/components/marketing/roll";
import { HomeMotion } from "@/components/marketing/home-motion";
import { MarketChart } from "@/components/marketing/market-chart";

export const metadata: Metadata = {
  title: "QuantForge: backtest Indian equity strategies before the bell",
  description:
    "Backtest systematic strategies on NSE and BSE history with STT, stamp duty, exchange charges and GST taken out of every simulated fill.",
};

const universe = [
  "NIFTY 50", "BANK NIFTY", "FINNIFTY", "SENSEX", "NIFTY MIDCAP 100", "NIFTY NEXT 50",
  "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "ITC", "LT", "SUNPHARMA", "TATAMOTORS",
];

const steps = [
  {
    time: "09:15",
    name: "Data",
    body: "Daily bars from Yahoo Finance with automatic NSE and BSE symbol resolution, or your own CSV. Kite Connect, Upstox and SmartAPI plug into the same interface.",
  },
  {
    time: "09:40",
    name: "Signals",
    body: "17 indicators, from SMA and SuperTrend to Aroon, Parabolic SAR and money flow, computed on the bars you loaded.",
  },
  {
    time: "10:20",
    name: "Strategy",
    body: "21 built in strategies behind a plugin registry. Every parameter becomes a field you can change before the run.",
  },
  {
    time: "11:00",
    name: "Backtest",
    body: "A vectorised engine with slippage, position sizing, stops, shorts and periodic rebalancing. Long runs go to a Celery worker.",
  },
];

// Round trip, delivery, ₹1,00,000 each leg. Rates from backend/app/backtesting/charges.py.
const note = [
  { item: "Securities transaction tax", rate: "0.1% each leg", amt: "200.00" },
  { item: "Exchange transaction charges", rate: "0.00297% each leg", amt: "5.94" },
  { item: "SEBI turnover fee", rate: "₹10 per crore each leg", amt: "0.20" },
  { item: "Stamp duty", rate: "0.015% on the buy", amt: "15.00" },
  { item: "GST", rate: "18% of exchange charges", amt: "1.07" },
];

// Every run reports these, grouped by the question each answers.
const metricGroups = [
  {
    q: "Was it worth the risk?",
    items: [
      ["Sharpe", "return per unit of total volatility"],
      ["Sortino", "the same, counting only downside swings"],
      ["Calmar", "yearly return against the worst drawdown"],
      ["Omega", "weight of gains against weight of losses"],
    ],
  },
  {
    q: "How bad did it get?",
    items: [
      ["Max drawdown", "deepest fall from a previous high"],
      ["VaR 95%", "a bad day you should expect once a month"],
      ["CVaR 95%", "the average of the days worse than that"],
      ["Ulcer index", "how deep and how long the drawdowns ran"],
    ],
  },
  {
    q: "Were the trades any good?",
    items: [
      ["Win rate", "share of trades that closed in profit"],
      ["Profit factor", "total won divided by total lost"],
      ["Alpha", "return the benchmark doesn't explain"],
      ["Beta", "how closely it moved with the benchmark"],
    ],
  },
];

function Rise({ as: Tag = "h2", lines, className }: { as?: "h2" | "p"; lines: string[]; className?: string }) {
  return (
    <Tag data-rise className={className}>
      {lines.map((l) => (
        <span key={l} className="block overflow-hidden pb-[0.08em]">
          <span data-rise-line className="block">
            {l}
          </span>
        </span>
      ))}
    </Tag>
  );
}

export default function HomePage() {
  return (
    <>
      <a
        href="#main"
        className="fixed left-4 top-4 z-50 -translate-y-24 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground focus:translate-y-0"
      >
        Skip to content
      </a>
      <MarketingNav />
      <HomeMotion />

      <main id="main">
        {/* 09:00 Pre-open */}
        <section id="pre-open" className="flex flex-col px-4 pb-20 pt-36 sm:px-6 md:pb-24 md:pt-48">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="lg:col-span-6">
            {/* Logo lockup is the page title; the tagline sits under it, smaller. */}
            <h1 className="display flex items-center gap-[0.25em] text-[clamp(3rem,7.5vw,6.5rem)]">
              <span className="block overflow-hidden pb-[0.08em]">
                <span className="flex animate-[rise_0.9s_var(--ease)_both] items-center gap-[0.25em] motion-reduce:animate-none">
                  <LogoMark className="h-[0.8em] w-[0.8em] shrink-0 text-primary" />
                  QuantForge
                </span>
              </span>
            </h1>
            <p className="display mt-6 text-[clamp(1.5rem,2.8vw,2.375rem)] text-foreground/90">
              <span className="block overflow-hidden pb-[0.08em]">
                <span className="block animate-[rise_0.9s_var(--ease)_0.1s_both] motion-reduce:animate-none">
                  Test the trade before the bell<span className="text-primary">.</span>
                </span>
              </span>
            </p>
            </div>
            <MarketChart className="hidden md:block lg:col-span-6 lg:-mr-6" />
          </div>
          <div className="mt-10 grid gap-8 md:grid-cols-12 md:items-end">
            <p className="max-w-[38rem] text-base leading-relaxed text-muted-foreground md:col-span-6">
              QuantForge backtests systematic strategies on NSE and BSE history and takes Indian charges out of every
              simulated fill. You see what a rule would have earned after STT, stamp duty and GST, before it costs you
              a rupee.
            </p>
            <div className="flex flex-wrap gap-3 md:col-span-6 md:justify-end">
              <RollButton href="/login">Open the demo desk</RollButton>
              <RollButton href="/register" variant="line">
                Create an account
              </RollButton>
            </div>
          </div>
        </section>

        {/* The demo universe as a moving tape. Names only; no prices are implied. */}
        <div className="overflow-hidden border-y border-border py-4" aria-label="Instruments in the demo universe">
          <ul className="sr-only">
            {universe.map((u) => (
              <li key={u}>{u}</li>
            ))}
          </ul>
          <div aria-hidden className="flex w-max animate-[tape_60s_linear_infinite] motion-reduce:animate-none">
            {[0, 1].map((k) => (
              <p key={k} className="num flex shrink-0 gap-10 pr-10 text-sm text-muted-foreground">
                {universe.map((u) => (
                  <span key={u}>
                    <span aria-hidden className="mr-2 inline-block h-1.5 w-1.5 -translate-y-px bg-primary" />
                    {u}
                  </span>
                ))}
              </p>
            ))}
          </div>
        </div>

        {/* 09:15 Open: the pipeline, a real sequence */}
        <section id="open" className="px-4 py-28 sm:px-6 md:py-28">
          <div className="grid gap-12 md:grid-cols-12">
            <div className="md:col-span-4">
              <Rise lines={["From a bar", "to a verdict."]} className="display text-[clamp(1.875rem,3vw,2.75rem)]" />
            </div>
            <ol className="border-t border-border md:col-span-8">
              {steps.map((s) => (
                <li key={s.name} className="grid grid-cols-[4.5rem_1fr] gap-x-6 gap-y-2 border-b border-border py-8 sm:grid-cols-[5rem_12rem_1fr]">
                  <span className="num pt-2 text-sm text-muted-foreground">{s.time}</span>
                  <h3 className="text-xl font-semibold leading-tight tracking-[-0.01em]">
                    {s.name}
                  </h3>
                  <p className="col-start-2 max-w-[34rem] text-[16px] leading-relaxed text-muted-foreground sm:col-start-3">
                    {s.body}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* 11:30 Midday: the contract note */}
        <section id="costs" className="border-t border-border bg-card px-4 py-28 sm:px-6 md:py-28">
          <div className="grid gap-16 md:grid-cols-12">
            <div className="md:col-span-5">
              <Rise
                lines={["The charges", "nobody draws", "on the chart."]}
                className="display text-[clamp(1.875rem,3vw,2.75rem)]"
              />
              <p className="mt-10 max-w-[30rem] text-base leading-relaxed text-muted-foreground">
                Buy ₹1,00,000 of one stock for delivery and sell it at the same price. The trade made nothing, and you
                are already ₹222.21 down, before slippage or brokerage. QuantForge charges every simulated fill the same
                way, buy leg and sell leg separately.
              </p>
            </div>
            <figure data-note className="self-end md:col-span-6 md:col-start-7">
              <figcaption className="flex justify-between border-b border-foreground pb-3 text-sm">
                <span className="font-semibold">Round trip, delivery</span>
                <span className="num text-muted-foreground">₹1,00,000 each leg</span>
              </figcaption>
              <table className="w-full text-left">
                <caption className="sr-only">Statutory charges on a ₹1,00,000 delivery round trip</caption>
                <thead className="sr-only">
                  <tr>
                    <th scope="col">Charge</th>
                    <th scope="col">Rate</th>
                    <th scope="col">Amount in rupees</th>
                  </tr>
                </thead>
                <tbody>
                  {note.map((r) => (
                    <tr key={r.item} data-row className="border-b border-border">
                      <th scope="row" className="py-4 pr-4 text-[15px] font-medium">
                        {r.item}
                        <span className="num mt-1 block text-xs font-normal text-muted-foreground">{r.rate}</span>
                      </th>
                      <td className="num py-4 text-right text-[15px]">₹{r.amt}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr data-row>
                    <th scope="row" className="pt-6 text-sm font-semibold">
                      Gone before the trade earns a paisa
                    </th>
                    <td className="num pt-6 text-right text-[clamp(1.75rem,3vw,2.25rem)] font-medium leading-none text-primary">
                      ₹222.21
                    </td>
                  </tr>
                </tfoot>
              </table>
            </figure>
          </div>
        </section>

        {/* 13:30 Afternoon: does the edge survive */}
        <section id="risk" className="px-4 py-28 sm:px-6 md:py-28">
          <Rise lines={["Does the edge", "survive the afternoon?"]} className="display text-[clamp(1.875rem,3vw,2.75rem)]" />
          <p className="mt-6 max-w-[38rem] text-base leading-relaxed text-muted-foreground">
            Twelve numbers on every run, grouped by the question they answer.
          </p>
          <div className="mt-12 grid gap-px overflow-hidden rounded-lg border border-border bg-border md:grid-cols-3">
            {metricGroups.map((g) => (
              <div key={g.q} className="bg-background p-6 md:p-8">
                <h3 className="text-lg font-semibold tracking-[-0.01em]">{g.q}</h3>
                <dl className="mt-6 space-y-4">
                  {g.items.map(([name, what]) => (
                    <div key={name}>
                      <dt className="text-[15px] font-semibold text-primary">{name}</dt>
                      <dd className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{what}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
          <div className="mt-16 grid gap-10 border-t border-border pt-10 md:grid-cols-12">
            <p className="text-[16px] leading-relaxed text-muted-foreground md:col-span-4">
              <strong className="mb-2 block font-semibold text-foreground">Walk-forward</strong>
              The same settings re-run on back-to-back slices of history, so one lucky stretch can&rsquo;t carry the
              whole result.
            </p>
            <p className="text-[16px] leading-relaxed text-muted-foreground md:col-span-4">
              <strong className="mb-2 block font-semibold text-foreground">Bootstrap intervals</strong>
              Block bootstrap puts a 95% range on Sharpe and CAGR. One lucky year shows up as a wide range, not a
              headline.
            </p>
            <p className="text-[16px] leading-relaxed text-muted-foreground md:col-span-4">
              <strong className="mb-2 block font-semibold text-foreground">Portfolio optimizer</strong>
              Five allocation methods, from equal weight to max Sharpe and risk parity, solved with constrained
              optimisation.
            </p>
          </div>
        </section>

        {/* 15:30 Close */}
        <section id="close" className="flex flex-col border-t border-border px-4 py-24 sm:px-6 md:py-32">
          <Rise lines={["Closing bell."]} className="display text-[clamp(2.5rem,5.5vw,4.75rem)]" />
          <div className="mt-12 grid gap-8 md:grid-cols-12 md:items-end">
            <p className="max-w-[34rem] text-base leading-relaxed text-muted-foreground md:col-span-6">
              The demo desk comes loaded with 20 NSE large caps, six index series and finished backtests. Change a
              parameter and run it again.
            </p>
            <div className="md:col-span-6 md:flex md:justify-end">
              <RollButton href="/login">Open the demo desk</RollButton>
            </div>
          </div>
        </section>
      </main>
      <div>
        <Footer />
      </div>
    </>
  );
}
