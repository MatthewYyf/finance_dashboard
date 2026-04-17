"use client";

import { useEffect, useState } from "react";
import { getMarketOverview } from "@/lib/api";

type MarketData = {
  symbol: string;
  price: number;
  change: number;
};

export default function MarketPage() {
  const [data, setData] = useState<MarketData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMarketOverview()
      .then(setData)
      .catch((err) => {
        console.error(err);
        setError("Could not load market data.");
      });
  }, []);

  return (
    <main className="mx-auto max-w-6xl flex-1 p-4 sm:p-8">
      <h1 className="mb-2 text-3xl font-bold text-white">Market</h1>
      <p className="mb-6 text-zinc-400">Overview of major symbols.</p>

      {error && (
        <p className="rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-3 text-red-200">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {data.map((item) => (
          <div
            key={item.symbol}
            className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4 shadow"
          >
            <h2 className="text-xl font-semibold text-white">{item.symbol}</h2>
            <p className="text-lg text-zinc-100">${item.price.toFixed(2)}</p>
            <p className={item.change >= 0 ? "text-green-400" : "text-red-400"}>
              {item.change >= 0 ? "+" : ""}
              {item.change.toFixed(2)}%
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
