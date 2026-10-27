import type { Metadata } from "next";

import { Footer } from "@/components/marketing/footer";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import { RollButton } from "@/components/marketing/roll";

export const metadata: Metadata = {
  title: "Market holiday: page not found | QuantForge",
  description: "There is no session on this page.",
};

export default function NotFound() {
  return (
    <>
      <MarketingNav />
      <main className="flex min-h-[70svh] flex-col justify-center px-4 pb-20 pt-32 sm:px-6">
        <h1 className="display text-[clamp(2.5rem,5.5vw,4.75rem)]">
          Market
          <br />
          holiday<span className="text-primary">.</span>
        </h1>
        <div className="mt-10 grid gap-8 md:grid-cols-12 md:items-end">
          <p className="max-w-[34rem] text-base leading-relaxed text-muted-foreground md:col-span-6">
            The exchange is shut and this address never listed. The order book is empty, and so is this page.
          </p>
          <div className="md:col-span-6 md:flex md:justify-end">
            <RollButton href="/">Back to the session</RollButton>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
