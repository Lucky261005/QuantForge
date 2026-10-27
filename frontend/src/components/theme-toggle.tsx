"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <Button variant="ghost" size="icon" className="h-9 w-9" aria-label="Toggle theme" />;
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-9 w-9"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      aria-label="Toggle theme"
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 opacity-100 transition-[transform,opacity] duration-200 ease-forge dark:-rotate-90 dark:scale-75 dark:opacity-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-75 opacity-0 transition-[transform,opacity] duration-200 ease-forge dark:rotate-0 dark:scale-100 dark:opacity-100" />
    </Button>
  );
}
