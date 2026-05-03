/**
 * XYRA — Analytics 5: Forecast Accuracy
 * Horizontal bar chart: accuracy % per product (worst → best).
 * Color scales: red < 50%, amber 50–75%, green > 75%.
 */

import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import type { ForecastAccuracyRow } from '../../services/api';

const accuracyColour = (pct: number): string => {
  if (pct >= 75) return '#10B981';
  if (pct >= 50) return '#F59E0B';
  return '#EF4444';
};

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload as ForecastAccuracyRow;
  return (
    <div className="bg-white border border-black/10 rounded-xl p-4 shadow-lg text-xs">
      <p className="font-serif text-sm mb-1">{row.product_id}</p>
      <p className="text-gray-400 mb-2">{row.category}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-6">
          <span className="text-gray-500">Accuracy</span>
          <span className="font-medium tabular-nums" style={{ color: accuracyColour(row.accuracy_pct) }}>
            {row.accuracy_pct}%
          </span>
        </div>
        <div className="flex justify-between gap-6">
          <span className="text-gray-500">MAPE</span>
          <span className="font-medium tabular-nums">{row.mape}%</span>
        </div>
        <div className="flex justify-between gap-6">
          <span className="text-gray-500">Method</span>
          <span className="font-medium capitalize">{row.method.replace('_', ' ')}</span>
        </div>
      </div>
    </div>
  );
};

interface Props {
  data: ForecastAccuracyRow[];
}

export function ForecastAccuracy({ data }: Props) {
  if (!data.length) return null;

  // Summary stats
  const avg = data.reduce((s, r) => s + r.accuracy_pct, 0) / data.length;
  const prophetCount = data.filter((r) => r.method === 'prophet').length;

  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col min-h-[420px]">
      {/* Header + summary */}
      <div className="flex items-start justify-between mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500">
          Forecast Accuracy (7-day MAPE)
        </h3>
        <div className="text-right">
          <div
            className="text-2xl font-serif"
            style={{ color: accuracyColour(avg) }}
          >
            {avg.toFixed(1)}%
          </div>
          <div className="text-[9px] uppercase tracking-widest text-gray-400">Avg accuracy</div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5 mb-4 text-[9px] font-medium uppercase tracking-widest text-gray-400">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />≥ 75%
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />50–75%
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />&lt; 50%
        </span>
      </div>

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 24, left: 0, bottom: 0 }}
            barSize={14}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#00000008" />
            <XAxis
              type="number"
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#999', fontSize: 10 }}
              tickFormatter={(v) => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="product_id"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#555', fontSize: 10 }}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#00000006' }} />
            <Bar dataKey="accuracy_pct" radius={[0, 4, 4, 0]}>
              {data.map((row) => (
                <Cell key={row.product_id} fill={accuracyColour(row.accuracy_pct)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-4 text-[9px] text-gray-400 uppercase tracking-widest">
        Prophet used for {prophetCount}/{data.length} products · MAPE = mean absolute % error on last 7 days
      </p>
    </div>
  );
}
