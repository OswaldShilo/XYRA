/**
 * XYRA — useWebSocket hook
 * Connects to /ws/dashboard, auto-reconnects, and exposes live twin data.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://localhost:8000/ws/dashboard';

export interface LiveSummary {
  total: number;
  critical: number;
  warning: number;
  safe: number;
}

export interface TwinData {
  product_id: string;
  category: string;
  current_stock: number;
  velocity: number;
  days_to_stockout: number;
  risk_level: 'CRITICAL' | 'WARNING' | 'SAFE';
  total_units_sold: number;
  last_updated: string;
}

export interface WsDashboardMessage {
  type: string;
  timestamp: string;
  data: {
    twins: Record<string, TwinData>;
    summary: LiveSummary;
    alerts: TwinData[];
  };
}

export function useWebSocket(enabled = true) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsDashboardMessage | null>(null);
  const [liveData, setLiveData] = useState<WsDashboardMessage['data'] | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (!enabled) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (e: MessageEvent) => {
      try {
        const msg: WsDashboardMessage = JSON.parse(e.data as string);
        setLastMessage(msg);
        if (msg.data) setLiveData(msg.data);
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (enabled) {
        reconnectRef.current = setTimeout(connect, 3000);
      }
    };

    ws.onerror = () => ws.close();
  }, [enabled]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, lastMessage, liveData };
}
