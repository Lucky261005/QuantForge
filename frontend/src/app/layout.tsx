import type { Metadata } from "next";
import { Archivo } from "next/font/google";
import localFont from "next/font/local";

import { Providers } from "@/components/providers";

import "./globals.css";

const archivo = Archivo({
  subsets: ["latin"],
  variable: "--font-archivo",
  axes: ["wdth"],
  display: "swap",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "QuantForge: backtest Indian equity strategies",
  description:
    "Research, backtest, and analyze systematic trading strategies with institutional-grade analytics.",
  // shortcut: localhost until a production domain exists; set NEXT_PUBLIC_SITE_URL when deploying
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  alternates: { canonical: "./" },
  openGraph: { type: "website", siteName: "QuantForge" },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${archivo.variable} ${geistMono.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
