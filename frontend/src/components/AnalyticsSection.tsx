/**
 * XYRA — Analytics Section
 * Fetches all 5 analytics endpoints for a static session and renders
 * InventoryHealth, DemandPatterns, SpikeDetection, HistoricalComparison,
 * and ForecastAccuracy in a single scrollable section.
 * Only shown when mode === 'static' and sessionId is available.
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { api } from '../services/api';
import type {
  InventoryHealthRow,
  DemandPatternsData,
  SpikeProduct,
  HistoricalComparisonData,
  ForecastAccuracyRow,
} from '../services/api';
import { InventoryHealth }        from './ui/InventoryHealth';
import { DemandPatterns }          from './ui/DemandPatterns';
import { SpikeDetection }          from './ui/SpikeDetection';
import { HistoricalComparison }    from './ui/HistoricalComparison';
import { ForecastAccuracy }        from './ui/ForecastAccuracy';

interface AnalyticsState {
  inventoryHealth:       InventoryHealthRow[]      | null;
  demandPatterns:        DemandPatternsData        | null;
  spikeDetection:        SpikeProduct[]            | null;
  historicalComparison:  HistoricalComparisonData  | null;
  forecastAccuracy:      ForecastAccuracyRow[]     | null;
  loading:               boolean;
  error:                 string | null;
}

interface Props {
  sessionId: string;
}

export function AnalyticsSection({ sessionId }: Props) {
  const [state, setState] = useState<AnalyticsState>({
    inventoryHealth: null,
    demandPatterns: null,
    spikeDetection: null,
    historicalComparison: null,
    forecastAccuracy: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function fetchAll() {
      try {
        const [inv, demand, spike, hist, acc] = await Promise.all([
          api.getAnalyticsInventoryHealth(sessionId),
          api.getAnalyticsDemandPatterns(sessionId),
          api.getAnalyticsSpikeDetection(sessionId),
          api.getAnalyticsHistoricalComparison(sessionId),
          api.getAnalyticsForecastAccuracy(sessionId),
        ]);

        if (cancelled) return;

        setState({
          inventoryHealth: inv.data,
          demandPatterns: demand.data,
          spikeDetection: spike.data,
          historicalComparison: hist.data,
          forecastAccuracy: acc.data,
          loading: false,
          error: null,
        });
      } catch (err) {
        if (cancelled) return;
        setState((s) => ({
          ...s,
          loading: false,
          error: err instanceof Error ? err.message : 'Failed to load analytics.',
        }));
      }
    }

    fetchAll();
    return () => { cancelled = true; };
  }, [sessionId]);

  if (state.loading) {
    return (
      <div className="py-16 flex flex-col items-center gap-4 text-gray-400">
        <div className="w-8 h-8 border border-black/20 border-t-black rounded-full animate-spin" />
        <p className="text-[10px] uppercase tracking-widest">Loading analytics…</p>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="py-10 px-8 bg-red-50 border border-red-100 rounded-3xl text-sm text-red-500">
        Analytics unavailable: {state.error}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-col gap-6"
    >
      {/* Section label */}
      <div className="flex items-center gap-4 pt-4">
        <div className="flex-1 h-px bg-black/8" />
        <span className="text-[9px] font-medium uppercase tracking-[0.25em] text-gray-400">
          Deep Analytics
        </span>
        <div className="flex-1 h-px bg-black/8" />
      </div>

      {state.inventoryHealth && (
        <InventoryHealth data={state.inventoryHealth} />
      )}
      {state.demandPatterns && (
        <DemandPatterns data={state.demandPatterns} />
      )}
      {state.spikeDetection && state.spikeDetection.length > 0 && (
        <SpikeDetection data={state.spikeDetection} />
      )}
      {state.historicalComparison && (
        <HistoricalComparison data={state.historicalComparison} />
      )}
      {state.forecastAccuracy && (
        <ForecastAccuracy data={state.forecastAccuracy} />
      )}
    </motion.div>
  );
}
