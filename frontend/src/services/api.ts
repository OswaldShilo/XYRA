/**
 * XYRA — REST API client
 * All calls to the FastAPI backend go through this module.
 */

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// ── Generic fetcher ────────────────────────────────────────────────────────────
async function req<T>(
  method: string,
  path: string,
  body?: unknown,
  isForm = false,
): Promise<T> {
  const init: RequestInit = { method };

  if (body !== undefined) {
    if (isForm) {
      init.body = body as FormData;
    } else {
      init.headers = { 'Content-Type': 'application/json' };
      init.body = JSON.stringify(body);
    }
  }

  const res = await fetch(`${BASE}${path}`, init);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as T;
}

// ── Typed response shapes ──────────────────────────────────────────────────────
export interface ApiResponse<T> {
  status: string;
  timestamp: string;
  data: T;
}

export interface QuickStats {
  total_products: number;
  critical: number;
  warning: number;
  safe: number;
}

export interface UploadResult {
  session_id: string;
  store_name: string;
  message: string;
  quick_stats: QuickStats;
}

export interface ProductClassification {
  product_id: string;
  category: string;
  current_stock: number;
  risk_level: string;
  priority: number;
  days_to_stockout: number;
  effective_days: number;
  forecast_7d_avg: number;
  forecast_14d_total: number;
  reorder_qty: number;
  reorder_by_date: string;
  spike_score: number;
  external_multiplier: number;
  reason: string;
}

export interface Dashboard {
  generated_at: string;
  total_products: number;
  critical_count: number;
  warning_count: number;
  safe_count: number;
  products: ProductClassification[];
}

export interface TwinSnapshot {
  product_id: string;
  category: string;
  current_stock: number;
  velocity: number;
  days_to_stockout: number;
  risk_level: string;
  total_units_sold: number;
  last_updated: string;
}

// ── API surface ───────────────────────────────────────────────────────────────
export const api = {
  // ── Shared ────────────────────────────────────────────────────────────────
  health: () =>
    req<{ status: string; sessions: number; twins: number }>('GET', '/health'),

  getEventSignals: (pincode: string, lookaheadDays = 14) =>
    req<ApiResponse<unknown>>(
      'GET',
      `/event-signals?pincode=${pincode}&lookahead_days=${lookaheadDays}`,
    ),

  getWeatherSignals: (pincode: string) =>
    req<ApiResponse<unknown>>('GET', `/weather-signals?pincode=${pincode}`),

  submitFeedback: (payload: {
    product_id: string;
    recommendation_id: string;
    accepted: boolean;
    actual_qty_ordered?: number;
    category?: string;
    manager_note?: string;
  }) => req<ApiResponse<unknown>>('POST', '/feedback', payload),

  getLearningStats: () => req<ApiResponse<unknown>>('GET', '/learning-stats'),

  // ── Static mode ───────────────────────────────────────────────────────────
  uploadCsv: (file: File, storeName: string, pincode: string, leadTime = 2) => {
    const form = new FormData();
    form.append('file', file);
    form.append('store_name', storeName);
    form.append('pincode', pincode);
    form.append('lead_time', String(leadTime));
    return req<ApiResponse<UploadResult>>('POST', '/upload-csv', form, true);
  },

  getDashboard: (sessionId: string) =>
    req<ApiResponse<Dashboard>>('GET', `/session/${sessionId}/dashboard`),

  getRecommendations: (sessionId: string, limit = 5) =>
    req<ApiResponse<unknown>>('GET', `/session/${sessionId}/recommendations?limit=${limit}`),

  getBriefing: (sessionId: string) =>
    req<ApiResponse<{ briefing: string; store_name: string }>>(
      'GET',
      `/session/${sessionId}/briefing`,
    ),

  getForecast: (sessionId: string, productId: string) =>
    req<ApiResponse<unknown>>('GET', `/session/${sessionId}/forecast/${productId}`),

  getChart: (sessionId: string) =>
    req<ApiResponse<{ chart: string }>>('GET', `/session/${sessionId}/chart`),

  getSessions: (limit = 10) =>
    req<ApiResponse<unknown[]>>('GET', `/sessions?limit=${limit}`),

  // ── Dynamic mode ──────────────────────────────────────────────────────────
  initTwins: (products: { product_id: string; category?: string; current_stock?: number; velocity?: number }[]) =>
    req<ApiResponse<unknown>>('POST', '/api/init-twins', { products }),

  saleEvent: (event: { product_id: string; qty_sold: number; store_id?: string }) =>
    req<ApiResponse<TwinSnapshot>>('POST', '/api/sale-event', event),

  restockEvent: (event: { product_id: string; qty_added: number }) =>
    req<ApiResponse<TwinSnapshot>>('POST', '/restock-event', event),

  getTwin: (productId: string) =>
    req<ApiResponse<TwinSnapshot>>('GET', `/twin/${productId}`),

  getAllTwins: () =>
    req<ApiResponse<Record<string, TwinSnapshot>>>('GET', '/twin/snapshot'),

  getAlerts: () =>
    req<ApiResponse<TwinSnapshot[]>>('GET', '/alerts'),

  manualSync: () =>
    req<ApiResponse<unknown>>('GET', '/api/sync'),
};
