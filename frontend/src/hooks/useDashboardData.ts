/**
 * XYRA — useDashboardData hook
 * Unified data layer for the dashboard.
 * Static mode: fetches once from /session/{id}/dashboard.
 * Dynamic mode: subscribes to the WebSocket live stream.
 */

import { useEffect, useState } from 'react';
import { api, Dashboard } from '../services/api';
import { useWebSocket, WsDashboardMessage } from './useWebSocket';

export type DashboardMode = 'static' | 'dynamic';

export interface DashboardState {
  mode: DashboardMode;
  loading: boolean;
  error: string | null;
  // Static
  sessionId: string | null;
  staticData: Dashboard | null;
  // Dynamic
  connected: boolean;
  liveMessage: WsDashboardMessage | null;
}

export function useDashboardData(
  mode: DashboardMode,
  sessionId: string | null,
): DashboardState {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [staticData, setStaticData] = useState<Dashboard | null>(null);

  const { connected, lastMessage, liveData } = useWebSocket(mode === 'dynamic');

  // Static mode: fetch once when sessionId is set
  useEffect(() => {
    if (mode !== 'static' || !sessionId) return;

    setLoading(true);
    setError(null);

    api
      .getDashboard(sessionId)
      .then((res) => setStaticData(res.data))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [mode, sessionId]);

  return {
    mode,
    loading,
    error,
    sessionId,
    staticData,
    connected,
    liveMessage: lastMessage,
  };
}
