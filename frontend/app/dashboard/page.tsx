import Link from "next/link";
import WatchlistCard from "@/components/WatchlistCard";
import { companies } from "@/lib/companies";

export default function DashboardPage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-12">
      <header className="mb-10 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Watchlist</h1>
          <p className="mt-2 text-sm text-neutral-600">
            {companies.length} companies tracked.
          </p>
        </div>
        <Link href="/" className="text-sm text-neutral-500 hover:text-neutral-900">
          ← Companies
        </Link>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {companies.map((company) => (
          <WatchlistCard key={company.slug} company={company} />
        ))}
      </div>
    </main>
  );
}
