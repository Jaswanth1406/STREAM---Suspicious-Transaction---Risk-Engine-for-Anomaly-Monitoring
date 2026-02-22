"use client";

import { motion } from "framer-motion";
import { api } from "@/lib/api";
import type { BidAnalysisResponse, BidAnalysisSummary } from "@/lib/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid,
  PieChart, Pie,
} from "recharts";
import { useState, useEffect } from "react";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function BidAnalysisPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<BidAnalysisSummary | null>(null);
  const [tendersData, setTendersData] = useState<BidAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [riskTier, setRiskTier] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('risk_score');
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    api.bidAnalysisSummary().then(setSummary).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, unknown> = { page, page_size: 15, sort_by: sortBy, sort_order: 'desc' };
    if (riskTier) params.risk_tier = riskTier;
    api.bidAnalysis(params).then(setTendersData).catch(() => {}).finally(() => setLoading(false));
  }, [page, riskTier, sortBy]);

  useEffect(() => { setPage(1); }, [riskTier, sortBy]);

  const tenders = tendersData?.tenders || [];
  const totalPages = tendersData?.total_pages || 1;

  const categoryChartData = summary?.top_categories?.slice(0, 8).map((c) => {
    const cat = c.category ?? 'Unknown';
    return {
      name: cat.length > 18 ? cat.slice(0, 18) + '...' : cat,
      risk: Math.round((c.avg_risk ?? 0) * 10) / 10,
      count: c.count ?? 0,
    };
  }) || [];

  const riskDistData = summary?.risk_distribution ? [
    { name: 'High', value: summary.risk_distribution.high ?? 0, color: '#e53e5c' },
    { name: 'Medium', value: summary.risk_distribution.medium ?? 0, color: '#d49a00' },
    { name: 'Low', value: summary.risk_distribution.low ?? 0, color: '#00b876' },
  ] : [];

  return (
    <div className="space-y-4">
      {/* Tab Bar */}
      <div className="flex items-center gap-1 border-b border-border pb-0 overflow-x-auto">
        <Link href="/dashboard" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Fraud Alerts</Link>
        <Link href="/dashboard/network" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Network Graph</Link>
        <span className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-accent-green tab-active whitespace-nowrap">Bid Analysis</span>
        <Link href="/dashboard/timeline" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">Timeline</Link>
        <Link href="/dashboard/chat" className="px-4 py-3 text-sm font-[var(--font-syne)] font-semibold text-muted hover:text-text whitespace-nowrap">AI Assistant</Link>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard label="Total Tenders" value={(summary.total_tenders ?? 0).toLocaleString()} color="text-text" />
          <StatCard label="Total Value" value={`₹${(summary.total_value_cr ?? 0).toLocaleString()}Cr`} color="text-accent-blue" />
          <StatCard label="Avg Risk Score" value={(summary.avg_risk_score ?? 0).toFixed(1)} color="text-accent-yellow" />
          <StatCard label="High Risk" value={(summary.risk_distribution?.high ?? 0).toLocaleString()} color="text-accent-red" />
        </div>
      )}

      {/* Charts Row */}
      {mounted && summary && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {/* Category Risk Chart */}
          <div className="bg-surface border border-border rounded-xl p-4">
            <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-3">Avg Risk by Category</h3>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryChartData} barSize={24}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d8dce8" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#6b7394", fontFamily: "monospace" }} axisLine={{ stroke: "#d8dce8" }} />
                  <YAxis tick={{ fontSize: 10, fill: "#6b7394", fontFamily: "monospace" }} axisLine={{ stroke: "#d8dce8" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #d8dce8", borderRadius: 8, fontSize: 12, fontFamily: "monospace", color: "#1a1f36" }} />
                  <Bar dataKey="risk" radius={[4, 4, 0, 0]}>
                    {categoryChartData.map((entry, i) => (
                      <Cell key={i} fill={entry.risk >= 30 ? '#e53e5c' : entry.risk >= 20 ? '#d49a00' : '#00b876'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Distribution Pie */}
          <div className="bg-surface border border-border rounded-xl p-4">
            <h3 className="text-sm font-[var(--font-syne)] font-bold text-text mb-3">Risk Distribution</h3>
            <div className="h-52 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistData}
                    cx="50%" cy="50%"
                    innerRadius={50} outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value.toLocaleString()}`}
                  >
                    {riskDistData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #d8dce8", borderRadius: 8, fontSize: 12, color: "#1a1f36" }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Filter & Sort */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted font-[var(--font-syne)]">Risk:</span>
          {['high', 'medium', 'low'].map((tier) => (
            <button
              key={tier}
              onClick={() => setRiskTier(riskTier === tier ? null : tier)}
              className={`text-[10px] px-2.5 py-1 rounded border font-[var(--font-space-mono)] capitalize transition-all ${
                riskTier === tier ? 'border-accent-green/50 text-accent-green bg-accent-green/10' : 'border-border text-muted hover:text-text'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted font-[var(--font-syne)]">Sort:</span>
          {[
            { key: 'risk_score', label: 'Risk' },
            { key: 'amount', label: 'Amount' },
            { key: 'num_tenderers', label: 'Bidders' },
          ].map((s) => (
            <button
              key={s.key}
              onClick={() => setSortBy(s.key)}
              className={`text-[10px] px-2.5 py-1 rounded border font-[var(--font-space-mono)] transition-all ${
                sortBy === s.key ? 'border-accent-blue/50 text-accent-blue bg-accent-blue/10' : 'border-border text-muted hover:text-text'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tenders Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-border flex items-center justify-between">
          <h3 className="text-sm font-[var(--font-syne)] font-bold text-text">Tender Analysis</h3>
          <span className="text-xs text-muted font-[var(--font-space-mono)]">
            {tendersData?.total?.toLocaleString() || 0} results
          </span>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Tender</th>
                  <th className="text-left text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Buyer</th>
                  <th className="text-right text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Amount</th>
                  <th className="text-center text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Bidders</th>
                  <th className="text-center text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Days</th>
                  <th className="text-right text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Risk</th>
                  <th className="text-center text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">ML</th>
                  <th className="text-left text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] px-4 py-3">Flags</th>
                </tr>
              </thead>
              <tbody>
                {tenders.map((t, i) => {
                  // Build flags from either nested .flags object or flat top-level fields
                  const flagSource = t.flags ?? t;
                  const flagKeys = ['flag_single_bidder', 'flag_zero_bidders', 'flag_short_window', 'flag_non_open', 'flag_high_value', 'flag_buyer_concentration', 'flag_round_amount', 'ml_anomaly_flag'] as const;
                  const activeFlags = flagKeys
                    .filter(k => (flagSource as unknown as Record<string, unknown>)[k] === 1 || (flagSource as unknown as Record<string, unknown>)[k] === true)
                    .map(k => k.replace(/^flag_/, '').replace(/^ml_anomaly_flag$/, 'ml').replace(/_/g, ' '));

                  const tenderTitle = t.title || t.tender_title || 'Untitled';
                  const amtDisplay = t.amount_display || (t.amount >= 1e7 ? `₹${(t.amount / 1e7).toFixed(1)}Cr` : t.amount >= 1e5 ? `₹${(t.amount / 1e5).toFixed(1)}L` : `₹${t.amount.toLocaleString()}`);
                  return (
                    <tr key={t.ocid || i} className="border-b border-border/50 hover:bg-surface2/30 transition-colors cursor-pointer" onClick={() => router.push(`/dashboard/bids/${encodeURIComponent(t.ocid || t.tender_id)}`)}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-[var(--font-syne)] text-text truncate max-w-[200px]">{tenderTitle}</p>
                            <p className="text-[10px] text-muted font-[var(--font-space-mono)]">{t.tender_id}</p>
                          </div>
                          <ExternalLink size={12} className="text-muted/40 flex-shrink-0" />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted font-[var(--font-syne)] max-w-[150px] truncate">{t.buyer_name}</td>
                      <td className="px-4 py-3 text-sm font-[var(--font-space-mono)] text-right text-text">{amtDisplay}</td>
                      <td className="px-4 py-3 text-sm font-[var(--font-space-mono)] text-center text-text">{t.num_tenderers}</td>
                      <td className="px-4 py-3 text-sm font-[var(--font-space-mono)] text-center text-muted">{t.duration_days}</td>
                      <td className="px-4 py-3 text-right">
                        <span className={`font-[var(--font-space-mono)] text-lg font-bold ${
                          t.risk_score >= 60 ? 'text-accent-red' : t.risk_score >= 30 ? 'text-accent-yellow' : 'text-accent-green'
                        }`}>
                          {Math.round(t.risk_score)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {t.predicted_suspicious ? (
                          <span className="text-[10px] bg-accent-red/10 text-accent-red border border-accent-red/30 px-2 py-0.5 rounded font-[var(--font-space-mono)]">
                            SUS {Math.round(t.suspicion_probability * 100)}%
                          </span>
                        ) : (
                          <span className="text-[10px] bg-accent-green/10 text-accent-green border border-accent-green/30 px-2 py-0.5 rounded font-[var(--font-space-mono)]">
                            CLEAN
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 flex-wrap">
                          {activeFlags.slice(0, 2).map((f, j) => (
                            <span key={j} className="text-[9px] bg-accent-red/10 text-accent-red border border-accent-red/20 px-1.5 py-0.5 rounded font-[var(--font-space-mono)] capitalize">
                              {f}
                            </span>
                          ))}
                          {activeFlags.length > 2 && <span className="text-[9px] text-muted">+{activeFlags.length - 2}</span>}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="flex items-center gap-1 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text disabled:opacity-30 transition-all"
          >
            <ChevronLeft size={14} /> Prev
          </button>
          <span className="text-sm font-[var(--font-space-mono)] text-muted">Page {page} / {totalPages}</span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
            className="flex items-center gap-1 px-3 py-2 rounded-lg border border-border text-sm text-muted hover:text-text disabled:opacity-30 transition-all"
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface border border-border rounded-xl p-4"
    >
      <p className="text-[10px] text-muted uppercase tracking-wider font-[var(--font-syne)] mb-1">{label}</p>
      <p className={`text-2xl font-[var(--font-space-mono)] font-bold ${color}`}>{value}</p>
    </motion.div>
  );
}
