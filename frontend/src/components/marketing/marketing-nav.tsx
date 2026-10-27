"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MarketClock, Wordmark } from "@/components/brand";
import { Roll, RollButton } from "@/components/marketing/roll";
import { ThemeToggle } from "@/components/theme-toggle";

const links = [
  { href: "/#open", label: "How it works" },
  { href: "/#costs", label: "Charges" },
  { href: "/#risk", label: "Risk" },
];

export function MarketingNav() {
  const pathname = usePathname();
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
      <nav aria-label="Main" className="flex h-20 items-center gap-8 px-4 sm:px-6">
        <Wordmark />
        <ul className="hidden items-center gap-7 md:flex">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                aria-current={pathname === l.href ? "page" : undefined}
                className="group inline-block py-1.5 text-base text-muted-foreground hover:text-foreground aria-[current=page]:text-foreground"
              >
                <Roll>{l.label}</Roll>
              </Link>
            </li>
          ))}
        </ul>
        <div className="ml-auto flex items-center gap-3">
          <MarketClock className="hidden text-sm xl:inline-flex" />
          <ThemeToggle />
          <Link href="/login" className="group hidden py-1.5 text-base font-medium sm:inline-block">
            <Roll>Log in</Roll>
          </Link>
          <RollButton href="/register" className="h-11 whitespace-nowrap px-4 text-sm sm:px-5 sm:text-base">
            Start free
          </RollButton>
        </div>
      </nav>
    </header>
  );
}
