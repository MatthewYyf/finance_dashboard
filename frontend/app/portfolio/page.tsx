"use client";

import { useEffect, useState } from "react";
import { getPortfolio } from "@/lib/api";

type Position = {
  symbol: string;
  shares: number;
  avg_cost: number;
};

type Portfolio = {
  total_value: number;
  daily_change: number;
  positions: Position[];
};

export default function PortfolioPage() {
  const [data, setData] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPortfolio()
      .then(setData)
      .catch((err) => {
        console.error(err);
        setError("Could not load portfolio.");
      });
  }, []);

  return (
    <main className="mx-auto max-w-6xl flex-1 p-4 sm:p-8">
      <h1 className="mb-2 text-3xl font-bold text-white">Portfolio</h1>
      <p className="mb-6 text-zinc-400">Holdings and performance snapshot.</p>

      {error && (
        <p className="mb-6 rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-3 text-red-200">
          {error}
        </p>
      )}

      {data && (
        <>
          <div className="mb-8 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <p className="text-sm text-zinc-400">Total value</p>
              <p className="text-2xl font-semibold text-white">
                ${data.total_value.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <p className="text-sm text-zinc-400">Daily change</p>
              <p
                className={
                  data.daily_change >= 0 ? "text-2xl font-semibold text-green-400" : "text-2xl font-semibold text-red-400"
                }
              >
                {data.daily_change >= 0 ? "+" : ""}
                {data.daily_change.toFixed(2)}%
              </p>
            </div>
          </div>

          <h2 className="mb-3 text-lg font-semibold text-white">Positions</h2>
          <div className="overflow-hidden rounded-2xl border border-zinc-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Symbol</th>
                  <th className="px-4 py-3 font-medium">Shares</th>
                  <th className="px-4 py-3 font-medium">Avg cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800 bg-zinc-950">
                {data.positions.map((p) => (
                  <tr key={p.symbol} className="text-zinc-200">
                    <td className="px-4 py-3 font-medium text-white">{p.symbol}</td>
                    <td className="px-4 py-3">{p.shares}</td>
                    <td className="px-4 py-3">
                      ${p.avg_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
