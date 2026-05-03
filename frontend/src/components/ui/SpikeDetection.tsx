/**
 * XYRA — Analytics 3: Spike Detection
 * Line chart with orange confidence band + spike badge for top 5 SKUs by spike_score.
 * Uses ComposedChart: two Area layers create the confidence ribbon effect.
 */

import React, { useState } from 'react';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { SpikeProduct } from '../../services/api';

interface Props {
  data: SpikeProduct[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-black/10 rounded-xl p-3 shadow-lg text-xs space-y-1">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p: any) => p.name !== 'upper' && p.name !== 'lower' && (
        <div key={p.name} className="flex justify-between gap-6">
          <span className="text-gray-500 capitalize">{p.name}</span>
          <span className="font-medium tabular-nums">{p.value?.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
};

export function SpikeDetection({ data }: Props) {
  const [activeIdx, setActiveIdx] = useState(0);

  if (!data.length) return null;

  const product = data[activeIdx];

  // Merge history + forecast into one series for the chart
  const chartData = [
    ...product.history.map((h) => ({ date: h.date, actual: h.actual })),
    ...product.forecast.map((f) => ({
      date: f.date,
      forecast: f.forecast,
      lower: f.lower,
      // The "band" trick: upper stores the WIDTH above lower, not the absolute value.
      // Recharts stacks the second Area on top of the first, so:
      //   Area 1: lower (fills from 0, transparent)
      //   Area 2: upper - lower (fills the band, orange)
      band: parseFloat((f.upper - f.lower).toFixed(2)),
    })),
  ];

  const splitDate = product.history[product.history.length - 1]?.date;

  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col min-h-[400px]">
      {/* Header + product tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500">
          Spike Detection — Forecast vs Actuals
        </h3>
        <div className="flex flex-wrap gap-2">
          {data.map((p, i) => (
            <button
              key={p.product_id}
              onClick={() => setActiveIdx(i)}
              className={`text-[9px] font-medium uppercase tracking-widest px-3 py-1 rounded-full transition-colors ${
                i === activeIdx
                  ? 'bg-black text-white'
                  : 'bg-black/5 text-gray-500 hover:bg-black/10'
              }`}
            >
              {p.product_id}
              {p.is_spike && (
                <span className="ml-1 text-[#FFB38E]">▲</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Spike badge */}
      {product.is_spike && (
        <div className="flex items-center gap-2 mb-4 px-4 py-2.5 bg-[#FFB38E]/15 border border-[#FFB38E]/30 rounded-xl w-fit">
          <span className="text-orange-500 font-bold text-sm">▲</span>
          <span className="text-[10px] font-medium uppercase tracking-widest text-gray-700">
            Demand spike detected — {product.spike_score.toFixed(1)}× forecast vs recent actuals
          </span>
        </div>
      )}

      {/* Chart */}
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"  stopColor="#FFB38E" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#FFB38E" stopOpacity={0.1} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#00000008" />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#999', fontSize: 9 }}
              dy={6}
              tickFormatter={(v) => v.slice(5)}
              interval={Math.max(0, Math.floor(chartData.length / 8) - 1)}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#999', fontSize: 9 }}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Confidence band: lower fills transparent, band fills orange on top */}
            <Area
              type="monotone"
              dataKey="lower"
              stroke="none"
              fill="transparent"
              stackId="band"
              legendType="none"
              name="lower"
            />
            <Area
              type="monotone"
              dataKey="band"
              stroke="none"
              fill="url(#bandGrad)"
              stackId="band"
              legendType="none"
              name="upper"
            />

            {/* Forecast line */}
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#FFB38E"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
              name="forecast"
            />

            {/* Actuals line */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#0A0A0A"
              strokeWidth={2}
              dot={false}
              name="actual"
            />

            {/* Split line: today */}
            {splitDate && (
              <ReferenceLine
                x={splitDate}
                stroke="#FFB38E"
                strokeDasharray="4 3"
                label={{ value: 'Today', fill: '#FFB38E', fontSize: 9, position: 'top' }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-4 text-[9px] text-gray-400 uppercase tracking-widest">
        Shaded band = 80% confidence interval · Dashed = forecast · Solid = actuals
      </p>
    </div>
  );
}
