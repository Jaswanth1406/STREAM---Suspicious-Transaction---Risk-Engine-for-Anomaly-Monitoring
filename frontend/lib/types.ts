// ── KPI Dashboard ──
export interface KPIData {
  active_flags: number;
  at_risk_value_cr: number;
  vendors_tracked: number;
  precision_rate: number;
  bid_rigging_detected: number;
  shell_networks_mapped: number;
  political_connections: number;
  false_positive_control: number;
  total_tenders_analyzed: number;
  high_risk_tenders: number;
  medium_risk_tenders: number;
  low_risk_tenders: number;
  total_bond_value_cr: number;
  unique_bond_purchasers: number;
  political_parties_linked: number;
}

// ── Alert Flags ──
export interface AlertFlags {
  flag_single_bidder: number;
  flag_zero_bidders: number;
  flag_short_window: number;
  flag_non_open: number;
  flag_high_value: number;
  flag_buyer_concentration: number;
  flag_round_amount: number;
  ml_anomaly_flag: number;
}

// ── Alert (union: electoral bond OR procurement) ──
export interface ApiAlert {
  // Common fields
  alert_id: string;
  alert_type: string;
  sub_type?: string;
  risk_score: number;
  confidence: number;
  risk_tier: string;
  title: string;
  evidence_strength: number;
  explanation?: string;

  // Electoral Bond fields
  purchaser_name?: string;
  total_bond_value?: number;
  total_bond_value_cr?: number;
  total_bonds?: number;
  parties_funded?: string[];
  flags_triggered?: string[];

  // Procurement alert fields (legacy/future)
  id?: string;
  tender_id?: string;
  buyer_name?: string;
  category?: string;
  procurement_method?: string;
  amount?: number;
  amount_display?: string;
  num_tenderers?: number;
  duration_days?: number;
  alert_type_display?: string;
  flags?: AlertFlags;
  risk_explanation?: string;
}

export interface AlertsResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  alerts: ApiAlert[];
}

// ── Network Graph ──
export interface NetworkNode {
  id: string;
  label: string;
  type: string;
  risk_score: number | null;
  risk_tier: string | null;
  size: number;
  color: string;
}

export interface NetworkEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
  label: string;
  color: string;
}

export interface NetworkGraphResponse {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    node_types: Record<string, number>;
    edge_types: Record<string, number>;
  };
}

// ── Vendor ──
export interface VendorConnection {
  type: string;
  cluster_size?: number;
  label: string;
  // legacy fields (may not be present)
  entity_name?: string;
  detail?: string;
  amount?: string | null;
  date?: string | null;
  risk_level?: string;
}

export interface VendorProfile {
  cin: string;
  company_name: string;
  company_status?: string;
  state?: string;
  composite_risk_score: number;
  risk_tier: string;
  sub_scores: {
    bid_pattern: number;
    shell_risk: number;
    political: number;
    financials: number;
  };
  bid_stats?: Record<string, unknown>;
  political_info?: Record<string, unknown>;
  shell_explanation?: string;
  connections: VendorConnection[];
  requires_human_review?: boolean;
  // legacy fields (may not be present)
  vendor_id?: string;
  status?: string;
  registered_address?: string;
  authorized_capital?: number;
  paidup_capital?: number;
  industry?: string;
  date_of_registration?: string;
  overall_risk_score?: number;
  total_tenders?: number;
  total_contract_value?: number;
  flags_triggered?: number;
  connections_count?: number;
  recent_tenders?: {
    tender_id: string;
    title: string;
    amount: number;
    risk_score: number;
    date: string;
  }[];
}

export interface VendorSearchResult {
  entity_id: string;
  company_name: string;
  cin: string;
  composite_risk_score: number;
  risk_tier: string;
  sub_scores?: {
    bid_pattern: number;
    shell_risk: number;
    political: number;
    financials: number;
  };
}

export interface VendorSearchResponse {
  total: number;
  results: VendorSearchResult[];
}

// ── Bid Analysis ──
export interface BidAnalysisTender {
  ocid: string;
  tender_id: string;
  title?: string;
  tender_title?: string;
  buyer_name: string;
  category: string;
  procurement_method: string;
  amount: number;
  amount_display?: string;
  num_tenderers: number;
  duration_days: number;
  risk_score: number;
  risk_tier: string;
  anomaly_score: number;
  flags?: AlertFlags;
  // Flat flag fields from backend
  flag_single_bidder?: number;
  flag_zero_bidders?: number;
  flag_short_window?: number;
  flag_non_open?: number;
  flag_high_value?: number;
  flag_buyer_concentration?: number;
  flag_round_amount?: number;
  ml_anomaly_flag?: number;
  risk_explanation: string;
  predicted_suspicious: number;
  suspicion_probability: number;
}

export interface BidAnalysisResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  tenders: BidAnalysisTender[];
}

// Raw backend shape for summary (keys may have emoji prefixes)
export interface BidAnalysisSummaryRaw {
  total_tenders: number;
  risk_distribution: Record<string, number>;
  flag_counts: Record<string, number>;
  top_categories: { 'tenderclassification/description': string; total: number; flagged: number; avg_risk: number; total_value: number }[];
  top_buyers: { 'buyer/name': string; total: number; flagged: number; avg_risk: number; total_value: number }[];
  amount_stats: { total: number; mean: number };
}

// Normalized shape used by the UI
export interface BidAnalysisSummary {
  total_tenders: number;
  total_value_cr: number;
  avg_risk_score: number;
  risk_distribution: { high: number; medium: number; low: number };
  flag_counts: Record<string, number>;
  top_categories: { category: string; count: number; avg_risk: number }[];
  top_buyers: { buyer: string; count: number; avg_risk: number; total_value_cr: number }[];
}

// ── Activity ──
export interface ActivityEvent {
  event_type: string;
  icon: string;
  title: string;
  subtitle: string;
  risk_tier?: string;
  risk_score: number | null;
  amount_cr?: number;
  entity_name?: string;
  party_name?: string;
  sort_key?: number;
  // legacy fields (may not be present)
  timestamp?: string;
  time_ago?: string;
  amount?: number;
  amount_display?: string;
  related_entity?: string;
  detail_id?: string;
}

export interface ActivityResponse {
  total: number;
  activities?: ActivityEvent[];
  events?: ActivityEvent[];
}

// ── Statistics ──
export interface RiskDistribution {
  bins: { range: string; count: number }[];
  mean: number;
  median: number;
  std: number;
  p95: number;
  p99: number;
}

export interface TopRiskBuyer {
  buyer_name: string;
  avg_risk_score: number;
  max_risk_score: number;
  total_tenders: number;
  flagged_tenders: number;
  total_value_cr: number;
  dominant_category: string;
  top_flags: string[];
}

export interface TopRiskBuyersResponse {
  buyers: TopRiskBuyer[];
}

export interface BondSummaryParty {
  party_name: string;
  total_received_cr: number;
  bond_count: number;
  unique_donors: number;
  avg_bond_cr: number;
  max_single_bond_cr: number;
  procurement_links: number;
}

export interface BondSummary {
  total_bond_value_cr: number;
  total_bonds: number;
  unique_purchasers: number;
  parties: BondSummaryParty[];
}

// ── ML Model ──
export interface ModelInfo {
  model_type: string;
  roc_auc: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  features_used: string[];
  feature_importance: Record<string, number>;
  training_samples: number;
  test_samples: number;
  cv_roc_auc_mean: number;
  cv_roc_auc_std: number;
}

// ── Chat ──
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
// ── Agent Chat ──
export interface AgentToolCall {
  tool: string;
  args: Record<string, unknown>;
}

export interface AgentChatRequest {
  messages: ChatMessage[];
  session_id?: string;
}

export interface AgentChatResponse {
  response: string;
  tool_calls?: AgentToolCall[];
  session_id?: string;
}

export interface AgentSSEEvent {
  type: 'token' | 'tool_start' | 'tool_end' | 'done';
  content?: string;
  tool?: string;
  input?: unknown;
  output_preview?: string;
}