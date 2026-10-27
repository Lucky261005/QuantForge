"use client";

import { Download, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDownloadAsset, useUploadAsset } from "@/hooks/use-market-data";

function defaultStart() {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 3);
  return d.toISOString().slice(0, 10);
}

export function MarketDataPanel() {
  const [symbol, setSymbol] = useState("RELIANCE");
  const [startDate, setStartDate] = useState(defaultStart());
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [uploadSymbol, setUploadSymbol] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const download = useDownloadAsset();
  const upload = useUploadAsset();

  function handleDownload(e: React.FormEvent) {
    e.preventDefault();
    download.mutate({ symbol: symbol.toUpperCase(), start_date: startDate, end_date: endDate, source: "yahoo_finance" });
  }

  function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !uploadSymbol.trim()) return;
    upload.mutate({ symbol: uploadSymbol.trim().toUpperCase(), file });
    e.target.value = "";
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market data</CardTitle>
        <CardDescription>
          Download from Yahoo Finance (auto-resolves NSE symbols, e.g. RELIANCE → RELIANCE.NS) or upload a CSV before
          backtesting a symbol — bars are cached and deduplicated.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6 sm:grid-cols-2">
        <form onSubmit={handleDownload} className="space-y-3">
          <p className="text-xs font-medium text-muted-foreground">Download</p>
          <div className="grid grid-cols-3 gap-2">
            <Input
              placeholder="RELIANCE"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="col-span-1"
            />
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="col-span-1" />
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="col-span-1" />
          </div>
          <Button type="submit" variant="outline" size="sm" disabled={download.isPending} className="w-full">
            <Download className="h-3.5 w-3.5" /> Download
          </Button>
        </form>

        <div className="space-y-3">
          <p className="text-xs font-medium text-muted-foreground">Upload CSV</p>
          <div className="flex gap-2">
            <Label htmlFor="upload-symbol" className="sr-only">
              Symbol
            </Label>
            <Input
              id="upload-symbol"
              placeholder="Symbol (e.g. TCS)"
              value={uploadSymbol}
              onChange={(e) => setUploadSymbol(e.target.value)}
            />
          </div>
          <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleFileSelected} />
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            disabled={!uploadSymbol.trim() || upload.isPending}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-3.5 w-3.5" /> Choose CSV file
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
