import Image from "next/image";
import CompanyCard from "@/components/CompanyCard";
import { companies } from "@/lib/companies";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-12">
      <header className="mb-10">
        <div className="flex items-center gap-3">
          <Image
            src="/livestock-bull.png"
            alt="LiveStock"
            width={40}
            height={40}
          />
          <h1 className="text-2xl font-bold text-neutral-900">LiveStock</h1>
        </div>
        <p className="mt-2 max-w-2xl text-sm text-neutral-600">
          LiveStock explores whether price history, technical indicators, and
          news sentiment carry signal about stock direction over short time
          horizons. Not a trading product.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {companies.map((company) => (
          <CompanyCard key={company.slug} company={company} />
        ))}
      </div>
    </main>
  );
}
