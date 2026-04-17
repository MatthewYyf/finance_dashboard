import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl flex-1 p-4 sm:p-8">
      <h1 className="mb-3 text-3xl font-bold text-white sm:text-4xl">
        Finance Dashboard
      </h1>
      <p className="mb-10 max-w-2xl text-lg text-zinc-400">
        Track your portfolio, watch the market, and read news from one place.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { href: "/portfolio", title: "Portfolio", desc: "Holdings and P&L" },
          { href: "/market", title: "Market", desc: "Indices and movers" },
          { href: "/news", title: "News", desc: "Headlines (coming soon)" },
        ].map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group rounded-2xl border border-zinc-800 bg-zinc-900 p-5 transition-colors hover:border-zinc-600 hover:bg-zinc-800/80"
          >
            <h2 className="text-lg font-semibold text-white group-hover:text-zinc-50">
              {card.title}
            </h2>
            <p className="mt-1 text-sm text-zinc-400">{card.desc}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
