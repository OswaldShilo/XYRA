/**
 * XYRA — Graph 2: Demand Signal Breakdown (Stacked Bar)
 * For each product category: how much of the predicted demand comes from
 * baseline sales vs event multiplier vs weather multiplier.
 */

import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell,
} from 'recharts';

interface CategorySignal {
  category: string;
  baseline: number;  // percentage of total demand
  event: number;
  weather: number;
}

// ── Mock data — replace with merged Layer 4/5/2 output from session ───────────
const MOCK_DATA: CategorySignal[] = [
  { category: 'Beverages',  baseline: 55, event: 30, weather: 15 },
  { category: 'Groceries',  baseline: 72, event: 22, weather: 6  },
  { category: 'Dairy',      baseline: 80, event: 12, weather: 8  },
  { category: 'Snacks',     baseline: 60, event: 35, weather: 5  },
  { category: 'Electronics',baseline: 88, event: 10, weather: 2  },
  { category: 'Bakery',     baseline: 65, event: 20, weather: 15 },
];

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s: number, p: any) => s + (p.value ?? 0), 0);
  return (
    <div className="bg-white border border-black/10 rounded-xl p-4 shadow-lg text-xs">
      <p className="font-serif text-base mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between gap-6 mb-1">
          <span className="flex items-center gap-2 text-gray-500 capitalize">
            <span
              className="w-2 h-2 rounded-full inline-block"
              style={{ backgroundColor: p.fill }}
            />
            {p.name}
          </span>
          <span className="font-medium tabular-nums">
            {p.value}%
          </span>
        </div>
      ))}
      <div className="border-t border-black/10 mt-2 pt-2 flex justify-between font-medium">
        <span>Total demand signal</span>
        <span>{total}%</span>
      </div>
    </div>
  );
};

interface SignalBreakdownProps {
  data?: CategorySignal[];
}

export function SignalBreakdown({ data = MOCK_DATA }: SignalBreakdownProps) {
  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col min-h-[380px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500">
          Demand Signal Breakdown
        </h3>
        <div className="flex items-center gap-5 text-[9px] font-medium uppercase tracking-widest text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-black inline-block" />Baseline
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#FFB38E] inline-block" />Event
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-300 inline-block" />Weather
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
            barSize={28}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#00000008"
            />
            <XAxis
              dataKey="category"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#999', fontSize: 10 }}
              dy={8}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#999', fontSize: 10 }}
              tickFormatter={(v) => `${v}%`}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />

            <Bar dataKey="baseline" name="Baseline" stackId="a" fill="#0A0A0A" radius={[0, 0, 4, 4]} />
            <Bar dataKey="event"    name="Event"    stackId="a" fill="#FFB38E" radius={[0, 0, 0, 0]} />
            <Bar dataKey="weather"  name="Weather"  stackId="a" fill="#FCD34D" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-4 text-[9px] text-gray-400 uppercase tracking-widest">
        Baseline = Layer 2 forecast · Event = Layer 4 multiplier · Weather = Layer 5 multiplier
      </p>
    </div>
  );
}
