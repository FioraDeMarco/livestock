"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Candle } from "@/lib/types";

export default function PriceChart({
  candles,
  color,
}: {
  candles: Candle[];
  color: string;
}) {
  if (candles.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center border border-neutral-200 text-sm text-neutral-400">
        Price history unavailable
      </div>
    );
  }

  return (
    <div className="h-64 w-full border border-neutral-200 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={candles}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value: string) => value.slice(5)}
            minTickGap={30}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            domain={["auto", "auto"]}
            tickFormatter={(value: number) => `$${value}`}
            width={60}
          />
          <Tooltip
            formatter={(value?: number | string | readonly (number | string)[]) => [
              `$${Number(value).toFixed(2)}`,
              "Close",
            ]}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke={color}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
