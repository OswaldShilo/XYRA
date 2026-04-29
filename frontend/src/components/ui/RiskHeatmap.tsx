/**
 * XYRA — Graph 1: SKU-Level Risk Heatmap
 * 7-day forward-looking grid: rows = top 10 SKUs, columns = days.
 * Cells coloured by predicted risk level (red / amber / green).
 */

import React from 'react';
import { cn } from '../../lib/utils';

type RiskLevel = 'critical' | 'warning' | 'safe';

interface SKURisk {
  sku: string;
  category: string;
  currentDays: number;
  days: RiskLevel[];
}

// ── Mock data — replace with backend /session/{id}/dashboard payload ──────────
const MOCK_DATA: SKURisk[] = [
  { sku: 'P0001', category: 'Beverages',    currentDays: 1.2, days: ['critical','critical','critical','critical','warning','warning','safe'] },
  { sku: 'P0007', category: 'Bakery',       currentDays: 2.8, days: ['critical','critical','warning','warning','safe','safe','safe'] },
  { sku: 'P0023', category: 'Dairy',        currentDays: 3.1, days: ['warning','warning','warning','safe','safe','safe','safe'] },
  { sku: 'P0011', category: 'Snacks',       currentDays: 4.5, days: ['warning','warning','safe','safe','safe','safe','safe'] },
  { sku: 'P0034', category: 'Groceries',    currentDays: 5.0, days: ['warning','safe','safe','safe','safe','safe','safe'] },
  { sku: 'P0042', category: 'Beverages',    currentDays: 6.2, days: ['warning','safe','safe','safe','safe','safe','safe'] },
  { sku: 'P0055', category: 'Electronics',  currentDays: 8.4, days: ['safe','safe','safe','safe','safe','safe','safe'] },
  { sku: 'P0062', category: 'Groceries',    currentDays: 9.1, days: ['safe','safe','safe','safe','safe','safe','safe'] },
  { sku: 'P0078', category: 'Dairy',        currentDays: 11.5,days: ['safe','safe','safe','safe','safe','safe','safe'] },
  { sku: 'P0091', category: 'Snacks',       currentDays: 14.0,days: ['safe','safe','safe','safe','safe','safe','safe'] },
];

const DAY_LABELS = ['D+1', 'D+2', 'D+3', 'D+4', 'D+5', 'D+6', 'D+7'];

const CELL_STYLES: Record<RiskLevel, string> = {
  critical: 'bg-red-500 text-white',
  warning:  'bg-amber-400 text-black',
  safe:     'bg-emerald-400 text-black',
};

const RISK_LABEL: Record<RiskLevel, string> = {
  critical: '●',
  warning:  '●',
  safe:     '●',
};

interface RiskHeatmapProps {
  data?: SKURisk[];
}

export function RiskHeatmap({ data = MOCK_DATA }: RiskHeatmapProps) {
  return (
    <div className="bg-white p-8 border border-black/5 rounded-3xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500">
          SKU Risk Heatmap — 7-Day Outlook
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

      {/* Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-separate border-spacing-1">
          <thead>
            <tr>
              <th className="text-left text-[9px] font-medium uppercase tracking-widest text-gray-400 pb-2 pr-4 w-32">
                SKU
              </th>
              <th className="text-[9px] font-medium uppercase tracking-widest text-gray-400 pb-2 pr-4 w-20 text-right">
                Days Left
              </th>
              {DAY_LABELS.map((d) => (
                <th
                  key={d}
                  className="text-center text-[9px] font-medium uppercase tracking-widest text-gray-400 pb-2 w-12"
                >
                  {d}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.sku} className="group">
                {/* SKU label */}
                <td className="pr-4 py-0.5">
                  <div className="font-serif text-sm leading-none">{row.sku}</div>
                  <div className="text-[9px] text-gray-400 mt-0.5">{row.category}</div>
                </td>

                {/* Days to stockout */}
                <td className="pr-4 py-0.5 text-right">
                  <span
                    className={cn(
                      'text-xs font-bold tabular-nums',
                      row.currentDays <= 3
                        ? 'text-red-500'
                        : row.currentDays <= 7
                        ? 'text-amber-500'
                        : 'text-emerald-500',
                    )}
                  >
                    {row.currentDays.toFixed(1)}d
                  </span>
                </td>

                {/* Day cells */}
                {row.days.map((risk, i) => (
                  <td key={i} className="py-0.5">
                    <div
                      className={cn(
                        'w-10 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold mx-auto transition-transform duration-150 group-hover:scale-105',
                        CELL_STYLES[risk],
                      )}
                      title={`${row.sku} D+${i + 1}: ${risk.toUpperCase()}`}
                    >
                      {RISK_LABEL[risk]}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-[9px] text-gray-400 uppercase tracking-widest">
        Forecast adjusted for event + weather multipliers · Sorted by urgency
      </p>
    </div>
  );
}
