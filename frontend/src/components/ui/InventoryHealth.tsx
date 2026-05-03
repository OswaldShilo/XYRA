/**
 * XYRA — Analytics 1: Inventory Health
 * Horizontal bar chart: top 15 SKUs by days-to-stockout, risk-coloured.
 */

import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import type { InventoryHealthRow } from '../../services/api';

const RISK_COLOUR: Record<string, string> = {
  CRITICAL: '#EF4444',
  WARNING:  '#F59E0B',
  SAFE:     '#10B981',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload as InventoryHealthRow;
  return (
    <div className="bg-white border border-black/10 rounded-xl p-4 shadow-lg text-xs">
      <p className="font-serif text-sm mb-1">{row.sku}</p>
      <p className="text-gray-500 mb-2">{row.category}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-6">
          <span className="text-gray-500">Days to stockout</span>
          <span className="font-medium tabular-nums">{row.days_to_stockout}d</span>
        </div>
        <div className="flex justify-between gap-6">
          <span className="text-gray-500">Current stock</span>
          <span className="font-medium tabular-nums">{row.current_stock} units</span>
        </div>
        <div className="flex justify-between gap-6">
          <span className="text-gray-500">Status</span>
          <span
            className="font-bold uppercase text-[9px] tracking-widest"
            style={{ color: RISK_COLOUR[row.risk_level] }}
          >
            {row.risk_level}
          </span>
        </div>
      </div>
    </div>
  );
};

interface Props {
  data: InventoryHealthRow[];
}

export function InventoryHealth({ data }: Props) {
  if (!data.length) return null;

  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col min-h-[420px]">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500">
          Inventory Health — Days to Stockout
        </h3>
        <div className="flex items-center gap-4 text-[9px] font-medium uppercase tracking-widest text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Critical
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />Warning
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />Safe
          </span>
        </div>
      </div>

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 24, left: 0, bottom: 0 }}
            barSize={14}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              stroke="#00000008"
            />
            <XAxis
              type="number"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#999', fontSize: 10 }}
              tickFormatter={(v) => `${v}d`}
            />
            <YAxis
              type="category"
              dataKey="sku"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#555', fontSize: 10 }}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#00000006' }} />
            <Bar dataKey="days_to_stockout" radius={[0, 4, 4, 0]}>
              {data.map((row) => (
                <Cell
                  key={row.sku}
                  fill={RISK_COLOUR[row.risk_level] ?? '#10B981'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-4 text-[9px] text-gray-400 uppercase tracking-widest">
        Sorted by urgency · Based on Layer 3 risk classification
      </p>
    </div>
  );
}
