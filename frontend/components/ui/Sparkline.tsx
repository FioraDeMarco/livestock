"use client";

import { Area, AreaChart, ResponsiveContainer } from "recharts";
import type { Candle } from "@/lib/types";

export default function Sparkline({
  candles,
  color,
}: {
  candles: Candle[];
  color: string;
}) {
  if (candles.length === 0) {
    return (
      <div className="flex h-16 w-full items-center">
        <div className="h-px w-full bg-neutral-200" />
      </div>
    );
  }

  return (
    <div className="h-16 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={candles} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
          <defs>
            <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.2} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="close"
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#spark-${color})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
