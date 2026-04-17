export default function NewsPage() {
  return (
    <main className="mx-auto max-w-6xl flex-1 p-4 sm:p-8">
      <h1 className="mb-2 text-3xl font-bold text-white">News</h1>
      <p className="mb-6 max-w-2xl text-zinc-400">
        Headlines and market commentary will show here once you connect a news or
        sentiment feed to the backend.
      </p>
      <div className="rounded-2xl border border-dashed border-zinc-700 bg-zinc-900/50 p-10 text-center text-zinc-500">
        No articles yet
      </div>
    </main>
  );
}
