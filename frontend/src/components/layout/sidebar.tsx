"use client";

import {
  BarChart3,
  FlaskConical,
  LayoutDashboard,
  NotebookPen,
  Settings,
  Star,
  TestTube2,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { MarketClock, Wordmark } from "@/components/brand";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui-store";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/strategies", label: "Strategy builder", icon: FlaskConical },
  { href: "/backtests", label: "Backtests", icon: TestTube2 },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/portfolio", label: "Portfolio", icon: Wallet },
  { href: "/watchlist", label: "Watchlist", icon: Star },
  { href: "/notes", label: "Research notes", icon: NotebookPen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const collapsed = useUiStore((s) => s.sidebarCollapsed);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-border bg-background transition-[width] duration-200 ease-forge lg:flex",
        collapsed ? "w-[76px]" : "w-64",
      )}
    >
      <div className="flex h-20 items-center px-5">
        <Wordmark compact={collapsed} />
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Primary">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group relative flex items-center gap-3 rounded-md px-3 py-3 text-[15px] font-medium transition-colors",
                active
                  ? "bg-accent text-foreground before:absolute before:inset-y-2 before:left-0 before:w-px before:bg-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <item.icon className="h-5 w-5 shrink-0 transition-transform duration-200 ease-forge group-hover:translate-x-0.5" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {!collapsed && (
        <div className="m-3 space-y-2 border-t border-border px-2 pt-4">
          <MarketClock />
        </div>
      )}
    </aside>
  );
}
