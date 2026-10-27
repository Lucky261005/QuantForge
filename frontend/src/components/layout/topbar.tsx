"use client";

import {
  BarChart3,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Menu,
  NotebookPen,
  Search,
  Settings,
  Star,
  TestTube2,
  Wallet,
  User,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";
import { useUiStore } from "@/store/ui-store";

const pageTitles: Record<string, string> = {
  "/dashboard": "Research dashboard",
  "/strategies": "Strategy builder",
  "/backtests": "Backtests",
  "/analytics": "Analytics",
  "/portfolio": "Paper portfolio",
  "/watchlist": "Watchlist",
  "/notes": "Research notes",
  "/settings": "Settings",
};

const mobileNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/strategies", label: "Strategy builder", icon: FlaskConical },
  { href: "/backtests", label: "Backtests", icon: TestTube2 },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/portfolio", label: "Portfolio", icon: Wallet },
  { href: "/watchlist", label: "Watchlist", icon: Star },
  { href: "/notes", label: "Research notes", icon: NotebookPen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Topbar() {
  const pathname = usePathname();
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen);
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  const title = pageTitles[pathname] ?? Object.entries(pageTitles).find(([p]) => pathname.startsWith(p))?.[1] ?? "";

  const initials =
    (user?.full_name || user?.username || "?")
      .split(" ")
      .map((s: string) => s[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "?";

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur sm:px-6">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation menu">
            <Menu className="h-5 w-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          {mobileNav.map((item) => (
            <DropdownMenuItem key={item.href} asChild>
              <Link href={item.href}>
                <item.icon className="mr-1 h-4 w-4" /> {item.label}
              </Link>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <h1 className="truncate text-base font-semibold tracking-[-0.02em] sm:text-xl">{title}</h1>

      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="outline"
          className="hidden h-11 w-72 justify-start gap-2.5 px-4 text-[15px] font-normal text-muted-foreground sm:inline-flex"
          onClick={() => setCommandPaletteOpen(true)}
        >
          <Search className="h-4 w-4" />
          Search
          <kbd className="ml-auto rounded border border-border bg-muted px-2 py-0.5 text-xs font-medium">Ctrl + K</kbd>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="sm:hidden"
          onClick={() => setCommandPaletteOpen(true)}
          aria-label="Open search"
        >
          <Search className="h-4 w-4" />
        </Button>

        <ThemeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="ml-1" aria-label="Open account menu">
              <Avatar className="h-9 w-9 border border-border">
                <AvatarFallback className="text-xs">{initials}</AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel className="font-normal">
              <p className="text-sm font-medium">{user?.full_name || user?.username}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/settings">
                <User /> Profile & settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => logout.mutate()}>
              <LogOut /> Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
