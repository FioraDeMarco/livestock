type PriceChangeProps = {
  change: number;
  percentChange: number;
  className?: string;
};

export default function PriceChange({
  change,
  percentChange,
  className = "",
}: PriceChangeProps) {
  const isPositive = change >= 0;
  const color = isPositive ? "text-green-600" : "text-red-600";
  const sign = isPositive ? "+" : "";

  return (
    <span className={`font-medium ${color} ${className}`}>
      {sign}
      {change.toFixed(2)} ({sign}
      {percentChange.toFixed(2)}%)
    </span>
  );
}
