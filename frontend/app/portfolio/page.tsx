"use client";

import { useEffect, useState } from "react";
import { getLivePortfolio, refreshPortfolio } from "@/lib/api";

type Position = {
  symbol: string;
  shares: number;
  avg_cost: number;
  updated_at: string;
  current_price: number | null;
  market_value: number | null;
  unrealized_gain: number | null;
};

type Portfolio = {
  total_value: number;
  cash: number;
  stock: number;
  updated_at: string | null;       // holdings snapshot timestamp
  quote_updated_at: string | null; // live quote timestamp
  positions: Position[];
  total_unrealized_gain: number;
};

export default function PortfolioPage() {
  const [data, setData] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadLivePortfolio = async (showLoader = false) => {
    try {
      if (showLoader) setLoading(true);
      setError(null);
      const portfolio = await getLivePortfolio();
      setData(portfolio);
    } catch (err) {
      console.error(err);
      setError("Could not load live portfolio.");
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError(null);

      // Refresh stored holdings snapshot in backend
      await refreshPortfolio();

      // Then reload live prices on top of the new holdings
      const livePortfolio = await getLivePortfolio();
      setData(livePortfolio);
    } catch (err) {
      console.error(err);
      setError("Could not refresh portfolio.");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadLivePortfolio(true);

    const interval = setInterval(() => {
      loadLivePortfolio(false);
    }, 20000);

    return () => clearInterval(interval);
  }, []);

  return (
    <main className="mx-auto max-w-7xl flex-1 p-4 sm:p-8">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="mb-2 text-3xl font-bold text-white">Portfolio</h1>
          <p className="text-zinc-400">
            Holdings update manually. Prices update automatically.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {refreshing ? "Refreshing holdings..." : "Refresh Portfolio"}
        </button>
      </div>

      {error && (
        <p className="mb-6 rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-3 text-red-200">
          {error}
        </p>
      )}

      {loading && <p className="text-zinc-400">Loading portfolio...</p>}

      {!loading && data && (
        <>
          <div className="mb-4 space-y-1">
            <p className="text-sm text-zinc-400">
              Portfolio updated:{" "}
              <span className="text-zinc-200">
                {data.updated_at ? new Date(data.updated_at).toLocaleString() : "Never"}
              </span>
            </p>
            <p className="text-sm text-zinc-400">
              Prices updated:{" "}
              <span className="text-zinc-200">
                {data.quote_updated_at
                  ? new Date(data.quote_updated_at).toLocaleString()
                  : "Never"}
              </span>
            </p>
          </div>

          <div className="mb-8 flex flex-row gap-4">
            <div className="flex-1 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 min-w-[170px]">
              <p className="text-sm text-zinc-400">Total value</p>
              <p className="text-2xl font-semibold text-white">
                ${data.total_value.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>

            <div className="flex-1 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 min-w-[170px]">
              <p className="text-sm text-zinc-400">Cash</p>
              <p className="text-2xl font-semibold text-white">
                ${data.cash.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>

            <div className="flex-1 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 min-w-[170px]">
              <p className="text-sm text-zinc-400">Stock</p>
              <p className="text-2xl font-semibold text-white">
                ${data.stock.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>

            <div className="flex-1 rounded-2xl border border-zinc-800 bg-zinc-900 p-5 min-w-[170px]">
              <p className="text-sm text-zinc-400">Unrealized Gain</p>
              <p
                className={`text-2xl font-semibold ${
                  data.total_unrealized_gain == null
                    ? "text-zinc-400"
                    : data.total_unrealized_gain >= 0
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {data.total_unrealized_gain != null
                  ? `${data.total_unrealized_gain >= 0 ? "+" : ""}$${Math.abs(
                      data.total_unrealized_gain
                    ).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}`
                  : "-"}
              </p>
            </div>
          </div>
     

          <h2 className="mb-3 text-lg font-semibold text-white">Open Portfolio</h2>
          <div className="overflow-hidden rounded-2xl border border-zinc-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Symbol</th>
                  <th className="px-4 py-3 font-medium">Shares</th>
                  <th className="px-4 py-3 font-medium">Avg cost</th>
                  <th className="px-4 py-3 font-medium">Current price</th>
                  <th className="px-4 py-3 font-medium">Market value</th>
                  <th className="px-4 py-3 font-medium">Unrealized gain</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800 bg-zinc-950">
                {data.positions.map((p) => (
                  <tr key={p.symbol} className="text-zinc-200">
                    <td className="px-4 py-3 font-medium text-white">{p.symbol}</td>
                    <td className="px-4 py-3">{p.shares}</td>
                    <td className="px-4 py-3">
                      ${p.avg_cost.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td className="px-4 py-3">
                      {p.current_price != null
                        ? `$${p.current_price.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}`
                        : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {p.market_value != null
                        ? `$${p.market_value.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}`
                        : "-"}
                    </td>
                    <td
                      className={`px-4 py-3 ${
                        p.unrealized_gain == null
                          ? "text-zinc-400"
                          : p.unrealized_gain >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {p.unrealized_gain != null
                        ? `${p.unrealized_gain >= 0 ? "+" : ""}$${Math.abs(
                            p.unrealized_gain
                          ).toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}`
                        : "-"}
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