import type { FundingRound } from "@/lib/types";

export default function FundingHistory({
  rounds,
}: {
  rounds: FundingRound[];
}) {
  return (
    <div className="border border-neutral-200">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
            <th className="px-4 py-3">Round</th>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Amount</th>
            <th className="px-4 py-3">Valuation</th>
            <th className="px-4 py-3">Lead Investor</th>
          </tr>
        </thead>
        <tbody>
          {rounds.map((round) => (
            <tr key={round.round} className="border-b border-neutral-100 last:border-0">
              <td className="px-4 py-3 font-medium text-neutral-900">{round.round}</td>
              <td className="px-4 py-3 text-neutral-600">{round.date}</td>
              <td className="px-4 py-3 text-neutral-600">{round.amount}</td>
              <td className="px-4 py-3 text-neutral-600">{round.valuation}</td>
              <td className="px-4 py-3 text-neutral-600">{round.leadInvestor}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-4 py-3 text-xs text-neutral-400">
        Figures are approximate, based on publicly reported funding news, and
        not official.
      </p>
    </div>
  );
}
