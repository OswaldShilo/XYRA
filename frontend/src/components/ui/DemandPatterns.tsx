/**
 * XYRA — Analytics 2: Demand Patterns
 * Area chart (daily trend) + day-of-week bar grid + category breakdown.
 */

import React from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { DemandPatternsData } from '../../services/api';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-black/10 rounded-xl p-3 shadow-lg text-xs">
      <p className="text-gray-500 mb-1">{label}</p>
      <p className="font-medium tabular-nums">{payload[0]?.value?.toFixed(0)} units</p>
    </div>
  );
};

interface Props {
  data: DemandPatternsData;
}

export function DemandPatterns({ data }: Props) {
  const { daily, by_dow, by_category } = data;

  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col gap-8">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 -mb-4">
        Demand Patterns
      </h3>

      {/* Daily trend */}
      {daily.length > 0 && (
        <div>
          <p className="text-[9px] uppercase tracking-widest text-gray-400 mb-3">
            Daily Sales Trend
          </p>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={daily} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="demandGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#FFB38E" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#FFB38E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#00000008" />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#999', fontSize: 9 }}
                  dy={6}
                  interval={Math.max(0, Math.floor(daily.length / 8) - 1)}
                  tickFormatter={(v) => v.slice(5)}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#999', fontSize: 9 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="units_sold"
                  stroke="#FFB38E"
                  strokeWidth={2}
                  fill="url(#demandGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* DOW + Category row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Day of week */}
        {by_dow.length > 0 && (
          <div>
            <p className="text-[9px] uppercase tracking-widest text-gray-400 mb-3">
              Average by Day of Week
            </p>
            <div className="h-[160px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={by_dow}
                  margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                  barSize={18}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#00000008" />
                  <XAxis
                    dataKey="day"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#999', fontSize: 9 }}
                    tickFormatter={(v) => v.slice(0, 3)}
                    dy={6}
                  />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#999', fontSize: 9 }} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: '#00000006' }} />
                  <Bar dataKey="avg_units" fill="#0A0A0A" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Category breakdown */}
        {by_category.length > 0 && (
          <div>
            <p className="text-[9px] uppercase tracking-widest text-gray-400 mb-3">
              Category Share
            </p>
            <div className="space-y-3">
              {by_category.slice(0, 6).map((c) => (
                <div key={c.category}>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-gray-600 font-medium">{c.category}</span>
                    <span className="text-gray-400 tabular-nums">{c.pct}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${c.pct}%`,
                        background: `linear-gradient(to right, #0A0A0A, #FFB38E)`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="text-[9px] text-gray-400 uppercase tracking-widest -mt-4">
        Source: Layer 2 forecast input · Pre-DSP cleaned data
      </p>
    </div>
  );
}
