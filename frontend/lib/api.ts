import type {
  KPIData, AlertsResponse, VendorProfile, VendorSearchResponse,
  NetworkGraphResponse, BidAnalysisResponse, BidAnalysisSummary, BidAnalysisSummaryRaw,
  ActivityResponse, RiskDistribution, BondSummary, ModelInfo,
  TopRiskBuyersResponse, ChatMessage, AgentChatRequest, AgentChatResponse, AgentSSEEvent,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://3gm76v9w-8000.inc1.devtunnels.ms';

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(body || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

function qs(params?: Record<string, unknown>): string {
  if (!params) return '';
  const entries = Object.entries(params)
    .filter(([, v]) => v != null && v !== '')
    .map(([k, v]) => [k, String(v)]);
  return entries.length ? '?' + new URLSearchParams(entries).toString() : '';
}

export const api = {
  // Health & Info
  health: () =>
    fetchApi<{ status: string; model_loaded: boolean; data_loaded: Record<string, number> }>('/'),
  modelInfo: () =>
    fetchApi<ModelInfo>('/model/info'),

  // Dashboard KPIs
  kpis: () =>
    fetchApi<KPIData>('/dashboard/kpis'),

  // Alerts
  alerts: (params?: Record<string, unknown>) =>
    fetchApi<AlertsResponse>(`/alerts${qs(params)}`),

  // Vendor
  vendor: (id: string) =>
    fetchApi<VendorProfile>(`/vendor/${encodeURIComponent(id)}`),
  vendorSearch: (query: string, limit = 20) =>
    fetchApi<VendorSearchResponse>(`/vendor/search/${encodeURIComponent(query)}?limit=${limit}`),

  // Network Graph
  networkGraph: (params?: Record<string, unknown>) =>
    fetchApi<NetworkGraphResponse>(`/network/graph${qs(params)}`),

  // Bid Analysis
  bidAnalysis: (params?: Record<string, unknown>) =>
    fetchApi<BidAnalysisResponse>(`/bid-analysis${qs(params)}`),
  bidAnalysisSummary: async (): Promise<BidAnalysisSummary> => {
    const raw = await fetchApi<BidAnalysisSummaryRaw>('/bid-analysis/summary');
    // Normalize emoji-prefixed risk distribution keys
    const rd = raw.risk_distribution || {};
    const parseRD = (key: string): number => {
      for (const [k, v] of Object.entries(rd)) {
        if (k.toLowerCase().includes(key)) return Number(v) || 0;
      }
      return 0;
    };
    return {
      total_tenders: raw.total_tenders,
      total_value_cr: Math.round((raw.amount_stats?.total || 0) / 1e7 * 100) / 100,
      avg_risk_score: (() => {
        // Estimate average risk from risk distribution tiers
        const h = parseRD('high');
        const m = parseRD('medium');
        const l = parseRD('low');
        const total = h + m + l;
        if (total === 0) return 0;
        // Use tier midpoints: high=75, medium=45, low=15
        return Math.round((h * 75 + m * 45 + l * 15) / total * 10) / 10;
      })(),
      risk_distribution: {
        high: parseRD('high'),
        medium: parseRD('medium'),
        low: parseRD('low'),
      },
      flag_counts: raw.flag_counts || {},
      top_categories: (raw.top_categories || []).map((c: { 'tenderclassification/description': string; total: number; avg_risk: number }) => ({
        category: c['tenderclassification/description'] || 'Unknown',
        count: c.total || 0,
        avg_risk: c.avg_risk || 0,
      })),
      top_buyers: (raw.top_buyers || []).map((b: { 'buyer/name': string; total: number; avg_risk: number; total_value: number }) => ({
        buyer: b['buyer/name'] || 'Unknown',
        count: b.total || 0,
        avg_risk: b.avg_risk || 0,
        total_value_cr: Math.round((b.total_value || 0) / 1e7 * 100) / 100,
      })),
    };
  },

  // Activity Feed
  activityRecent: (params?: Record<string, unknown>) =>
    fetchApi<ActivityResponse>(`/activity/recent${qs(params)}`),

  // Statistics
  riskDistribution: () =>
    fetchApi<RiskDistribution>('/stats/risk-distribution'),
  topRiskBuyers: (limit = 20, minTenders = 5) =>
    fetchApi<TopRiskBuyersResponse>(`/stats/top-risk-buyers?limit=${limit}&min_tenders=${minTenders}`),
  bondSummary: () =>
    fetchApi<BondSummary>('/stats/bond-summary'),

  // ML Predictions
  predict: (data: Record<string, unknown>) =>
    fetchApi<{ predicted_suspicious: number; suspicion_probability: number; predicted_risk_tier: string; risk_factors: Record<string, number> }>(
      '/predict',
      { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } },
    ),

  // Agent Chat
  agent: {
    chat: (request: AgentChatRequest) =>
      fetchApi<AgentChatResponse>(
        '/agent/chat',
        { method: 'POST', body: JSON.stringify(request), headers: { 'Content-Type': 'application/json' } },
      ),
    
    chatStream: (request: AgentChatRequest): EventSource => {
      const url = new URL(`${API_BASE}/agent/chat/stream`);
      const eventSource = new EventSource(url.href);
      
      // Send the request body by posting to the URL with body
      // Note: EventSource doesn't support POST directly, so we'll need to use fetch with ReadableStream
      return eventSource;
    },

    // Alternative: fetch-based streaming
    chatStreamFetch: async (request: AgentChatRequest, onEvent: (event: AgentSSEEvent) => void) => {
      const res = await fetch(`${API_BASE}/agent/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error('Response body is empty');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          onEvent({ type: 'done' });
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              onEvent(event);
            } catch (e) {
              console.error('Failed to parse SSE event:', line, e);
            }
          }
        }
      }
    },
  },
};
