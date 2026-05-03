/**
 * XYRA — Analytics 4: Historical Comparison
 * Monthly bar chart with MoM % line overlay + YoY category table.
 */

import React from 'react';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { HistoricalComparisonData } from '../../services/api';

interface Props {
  data: HistoricalComparisonData;
}

const MoMTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-black/10 rounded-xl p-3 shadow-lg text-xs space-y-1">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between gap-6">
          <span className="text-gray-500 capitalize">{p.name}</span>
          <span className="font-medium tabular-nums">
            {p.name === 'mom_pct' ? `${p.value?.toFixed(1)}%` : p.value?.toFixed(0)}
          </span>
        </div>
      ))}
    </div>
  );
};

export function HistoricalComparison({ data }: Props) {
  const { monthly, mom, yoy } = data;

  if (!monthly.length) return null;

  // Merge monthly volumes with MoM % for the composed chart
  const chartData = monthly.map((m) => {
    const momRow = mom.find((r) => r.month === m.month);
    return {
      month: m.month.slice(0, 7),
      units_sold: m.units_sold,
      mom_pct: momRow?.mom_pct ?? null,
    };
  });

  // Detect years in YoY data
  const yoyYears = yoy.length > 0
    ? Object.keys(yoy[0]).filter((k) => k !== 'category' && k !== 'year' && k !== 'units_sold')
    : [];

  const YEAR_COLOURS = ['#0A0A0A', '#FFB38E', '#F59E0B', '#6B7280'];

  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col gap-8">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 -mb-4">
        Historical Comparison
      </h3>

      {/* Monthly trend + MoM % */}
      <div>
        <p className="text-[9px] uppercase tracking-widest text-gray-400 mb-3">
          Monthly Volume &amp; MoM Growth
        </p>
        <div className="flex items-center gap-5 mb-3 text-[9px] font-medium uppercase tracking-widest text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-sm bg-black inline-block" />Volume
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-0.5 bg-[#FFB38E] inline-block" />MoM %
          </span>
        </div>
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 4, right: 32, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#00000008" />
              <XAxis
                dataKey="month"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#999', fontSize: 9 }}
                dy={6}
                tickFormatter={(v) => v.slice(2)}
                interval={Math.max(0, Math.floor(chartData.length / 8) - 1)}
              />
              <YAxis
                yAxisId="vol"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#999', fontSize: 9 }}
              />
              <YAxis
                yAxisId="pct"
                orientation="right"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#999', fontSize: 9 }}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip content={<MoMTooltip />} cursor={{ fill: '#00000006' }} />
              <ReferenceLine yAxisId="pct" y={0} stroke="#00000015" />
              <Bar yAxisId="vol" dataKey="units_sold" fill="#0A0A0A" radius={[3, 3, 0, 0]} barSize={18} name="units" />
              <Line
                yAxisId="pct"
                type="monotone"
                dataKey="mom_pct"
                stroke="#FFB38E"
                strokeWidth={2}
                dot={false}
                name="mom_pct"
                connectNulls
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* YoY per-category table */}
      {yoy.length > 0 && yoyYears.length > 1 && (
        <div>
          <p className="text-[9px] uppercase tracking-widest text-gray-400 mb-3">
            Year-on-Year by Category
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-separate border-spacing-y-1">
              <thead>
                <tr>
                  <th className="text-left text-[9px] font-medium uppercase tracking-widest text-gray-400 pb-2 pr-6">Category</th>
                  {yoyYears.map((yr, i) => (
                    <th
                      key={yr}
                      className="text-right text-[9px] font-medium uppercase tracking-widest pb-2 px-3"
                      style={{ color: YEAR_COLOURS[i % YEAR_COLOURS.length] }}
                    >
                      {yr}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {yoy.map((row: any) => (
                  <tr key={row.category ?? row.year} className="group">
                    <td className="pr-6 py-1 font-medium text-gray-700">{row.category ?? row.year}</td>
                    {yoyYears.map((yr, i) => (
                      <td key={yr} className="text-right px-3 py-1 tabular-nums text-gray-600">
                        {row[yr]?.toLocaleString() ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p className="text-[9px] text-gray-400 uppercase tracking-widest -mt-4">
        Source: cleaned sales history · Layer 1 output
      </p>
    </div>
  );
}
